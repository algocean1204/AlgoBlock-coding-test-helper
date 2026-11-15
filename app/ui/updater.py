"""새 버전 확인과 업데이트. 표준 라이브러리만 쓴다.

흐름: 확인(GitHub의 최신 릴리스) → 알림(화면 위쪽 막대) → 받기 → 무결성 확인(SHA-256) → 바꾸기 → 다시 켜기.
- 확인: 켤 때(마지막 확인에서 24시간이 지났으면)와 그 뒤 24시간마다. 실패하면 1시간에서 시작해 두 배씩, 최대 6시간 간격으로
  다시 묻고 성공하면 24시간으로 돌아간다. 확인 하나는 45초 안에 끝나지 않으면 실패로 친다. 설정에서 끌 수 있다.
- 받기와 바꾸기는 묶인 앱(PyInstaller)에서만 한다. 소스에서 실행하면 확인만 한다(git으로 받는다).
- macOS: dmg를 읽기 전용으로 붙여 새 .app을 지금 앱 옆에 복사하고, 앱이 끝난 뒤 작은 셸 스크립트가 바꿔 끼우고 다시 연다.
- Windows: 새 exe를 지금 exe 옆에 복사하고, 앱이 끝난 뒤 PowerShell 스크립트가 바꿔 끼우고 다시 연다(새 앱이 켜지지 않으면 되돌린다).
- 받은 파일은 자료 폴더의 updates/<버전>/에 둔다. 릴리스에 적힌 해시와 다르면 지우고 설치하지 않는다.
"""

import contextlib
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "0.1.1"  # 앱의 버전은 여기 한 곳에 둔다(algoblock.spec과 build_mac.sh가 이 줄을 읽는다)
REPO = "algocean1204/AlgoBlock-coding-test-helper"
LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOADS = f"https://github.com/{REPO}/releases/download/"  # 받는 주소는 이 저장소의 릴리스 파일만
PAGES = f"https://github.com/{REPO}/"
SUMS = "SHA256SUMS"
BUNDLE_ID = "io.github.algocean1204.algoblock"
WINDOWS_ASSET = "AlgoBlock-windows-x64.exe"  # Windows 릴리스 파일 이름은 여기 한 곳에 둔다
DAY = 24 * 60 * 60  # 확인 주기
RETRY, RETRY_MAX = 60 * 60, 6 * 60 * 60  # 실패하면 1시간 → 2시간 → 4시간 → 6시간 …
LIMIT = 45  # 확인 하나의 시간 한도(초)
TICK = 60  # 일정을 보는 간격(초). 잠자기에서 깨어나도 벽시계로 다시 맞춘다
MAX_SIZE = 2 * 1024 ** 3
DIR = Path(tempfile.gettempdir()) / "algoblock-updates"  # 서버가 자료 폴더 아래(updates)로 바꾼다
BUSY = ("downloading", "installing", "restarting")

LOCK = threading.Lock()
FILE_LOCK = threading.RLock()  # 설정 파일(settings.json)
NOW = {"state": "idle", "latest": None, "progress": 0, "message": "", "file": ""}
STARTED = []
PLAN = {"due": 0.0, "fails": 0}  # 다음 자동 확인 시각(벽시계)과 잇단 실패 수
CHECKING = []  # 돌고 있는 확인(하나만): (스레드, 결과를 담을 목록)

# 앱이 끝나기를 기다렸다가 새 앱으로 바꿔 끼우고 다시 연다. 옛 앱은 바꿔 끼우는 동안만 옆에 두고, 실패하면 되돌린다.
SWAP_SH = r"""#!/bin/sh
# 쓰는 법: sh swap.sh <앱 프로세스 번호> <지금 앱 경로> <옆에 둔 새 앱 경로>
pid=$1 app=$2 new=$3
old="$(dirname "$app")/.$(basename "$app").old"
n=0
while kill -0 "$pid" 2>/dev/null; do
  n=$((n + 1))
  if [ "$n" -gt 600 ]; then echo "앱이 끝나지 않아 바꾸지 않았다"; rm -rf "$new"; exit 1; fi
  sleep 0.1
done
rm -rf "$old"
if mv "$app" "$old"; then
  if mv "$new" "$app"; then rm -rf "$old"; echo "바꿨다"; else rm -rf "$app"; mv "$old" "$app"; rm -rf "$new"; echo "새 앱을 넣지 못해 되돌렸다"; fi
else
  rm -rf "$new"; echo "옛 앱을 옮기지 못해 바꾸지 않았다"
fi
open "$app"
"""

# Windows: 앱(onefile이면 풀어 놓는 부모 프로세스까지)이 끝나기를 기다렸다가 새 exe로 바꿔 끼우고 다시 연다. 값($app 등)은 swap_ps1()이 위에 붙인다.
# 실행 중인 exe도 이름은 바꿀 수 있지만, 끝난 뒤에만 건드린다($wait초 안에 끝나지 않으면 아무것도 바꾸지 않는다).
# 새 앱의 로컬 서버($url)가 $health초 안에 응답하지 않으면(열리지 않음, 오류로 끝남, 떠 있지만 깨짐) 새 앱을 끝내고 옛 exe를 되돌려 연다.
# 백신이 새 파일을 잠깐 잡는 일이 있어 옮기기는 몇 번 다시 한다. 되돌리기에 성공했을 때만 새 exe를 지운다(둘 다 잃지 않게).
SWAP_PS1 = r"""
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding $false
$waited = $false
$script:opened = $false
function Say([string]$text) {
  try { [IO.File]::AppendAllText($log, ('{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $text) + "`r`n", $utf8) } catch { }
}
function Move-Retry([string]$from, [string]$to) {
  # 막 복사한 큰 exe는 백신이 검사하느라 한동안 잡고 있을 수 있다. 60초까지 다시 하고, 다시 했거나 못 했으면 까닭을 남긴다
  $until = (Get-Date).AddSeconds(60)
  $tries = 0
  $last = ''
  while ($true) {
    try {
      [IO.File]::Move($from, $to)
      if ($tries) { Say ('옮겼다(' + $tries + '번 다시 함): ' + $from + ' -> ' + $to + ' / 앞의 까닭: ' + $last) }
      return $true
    } catch {
      $last = $_.Exception.Message
    }
    $tries++
    if ((Get-Date) -gt $until) { break }
    Start-Sleep -Milliseconds 500
  }
  Say ('옮기지 못했다: ' + $from + ' -> ' + $to + ' / ' + $last)
  return $false
}
function Remove-Retry([string]$path) {
  for ($i = 0; $i -lt 40; $i++) {
    try { if ([IO.File]::Exists($path)) { [IO.File]::Delete($path) }; return } catch { Start-Sleep -Milliseconds 500 }
  }
  Say ('지우지 못했다(다음에 켤 때 지운다): ' + $path)
}
function Open-App {
  try {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $app
    $info.UseShellExecute = $true  # 이 스크립트의 출력 파일(swap-out.log)을 새 앱에 물려주지 않는다(환경은 물려준다). 오류 창은 띄우지 않는다(ErrorDialog 기본 꺼짐)
    $info.WorkingDirectory = [IO.Path]::GetDirectoryName($app)
    $process = [Diagnostics.Process]::Start($info)
    $script:opened = $true
    Say ('열었다: ' + $app)
    return $process
  } catch {
    Say ('열지 못했다: ' + $_.Exception.Message)
    return $null
  }
}
function Test-Served {
  try {
    $request = [Net.WebRequest]::Create($url)
    $request.Proxy = $null
    $request.Timeout = 3000
    $response = $request.GetResponse()
    $ok = [int]$response.StatusCode -eq 200
    $response.Close()
    return $ok
  } catch {
    return $false
  }
}
function Stop-Tree($process) {
  # onefile은 부모와 자식 둘이다. 자식(앱)까지 끝내야 exe를 놓는다. 먼저 창을 닫게 해(/F 없이) 부모가 풀어 놓은 폴더를 치울 틈을 주고, 5초 안에 안 끝나면 강제로
  $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
  try { $null = & $taskkill /PID ([string]$process.Id) /T 2>&1 } catch { }
  try { if ($process.WaitForExit(5000)) { return } } catch { }
  try { $null = & $taskkill /PID ([string]$process.Id) /T /F 2>&1 } catch { }
  try { $null = $process.WaitForExit(10000) } catch { }
}
function Undo-Swap {
  # 새 exe를 옆으로 치우고 옛 exe를 제자리에. 새 exe가 이미 없으면(백신이 격리 등) 치우기는 건너뛴다.
  # 옛 exe를 되돌리지 못하면 새 exe도 다시 제자리에 둔다(앱이 없어지지 않게)
  if ([IO.File]::Exists($app) -and -not (Move-Retry $app $new)) {
    Say '새 앱을 치우지 못해 되돌리지 못했다'
    return
  }
  if (Move-Retry $old $app) {
    Remove-Retry $new
    Say '되돌렸다'
  } else {
    if ([IO.File]::Exists($new)) { $null = Move-Retry $new $app }
    Say '옛 앱을 되돌리지 못했다'
  }
}
try {
  Say ('스크립트 시작: PowerShell ' + $PSVersionTable.PSVersion + ', PID ' + $PID)  # 진단: 여기까지 왔는지
  # 앱의 프로세스를 먼저 잡아 둔다(끝난 뒤 그 번호를 다른 프로세스가 받아도 헷갈리지 않게). 잡은 뒤에 '기다리는 중' 표시를 남긴다
  # 앱 자신($ids[0])을 잡지 못하면 끝나기를 기다릴 수 없으니 바꾸지 않는다(표시를 남기지 않아 앱도 끝나지 않는다)
  $procs = @()
  foreach ($id in $ids) {
    try {
      $p = [Diagnostics.Process]::GetProcessById($id); $null = $p.Handle; $procs += $p
    } catch {
      if ($id -eq $ids[0]) {
        Say '앱 프로세스를 잡지 못해 바꾸지 않았다'
        Remove-Retry $new
        exit 1
      }
    }
  }
  [IO.File]::WriteAllText($ready, 'waiting')
  Say ('시작: ' + $app)
  $deadline = (Get-Date).AddSeconds($wait)
  foreach ($p in $procs) {
    $left = [int][Math]::Max(0, ($deadline - (Get-Date)).TotalMilliseconds)
    if (-not $p.WaitForExit($left)) {
      Remove-Retry $new
      if ($p.Id -eq $ids[0]) {
        Say '앱이 끝나지 않아 바꾸지 않았다'
      } else {
        # 앱은 끝났는데 풀어 놓은 파일을 치우는 부모 프로세스가 남았다. 바꾸지 않고, 사용자가 빈손이 되지 않게 옛 앱을 다시 연다
        Say '부모 프로세스가 끝나지 않아 바꾸지 않았다'
        $null = Open-App
      }
      exit 1
    }
  }
  $waited = $true
  Remove-Retry $old
  if (-not (Move-Retry $app $old)) {
    Say '옛 앱을 옮기지 못해 바꾸지 않았다'
    Remove-Retry $new
    $null = Open-App
    exit 1
  }
  if (-not (Move-Retry $new $app)) {
    if (Move-Retry $old $app) {
      Remove-Retry $new
      Say '새 앱을 넣지 못해 되돌렸다'
    } else {
      Say '새 앱을 넣지 못했고 옛 앱도 되돌리지 못했다'
    }
    $null = Open-App
    exit 1
  }
  $launched = Get-Date
  $started = Open-App
  $served = $false
  if ($started) {
    $until = $launched.AddSeconds($health)
    while ((Get-Date) -lt $until) {
      if (Test-Served) {
        $served = $true
        Say ('응답했다: {0:N1}초 (한도 {1}초)' -f ((Get-Date) - $launched).TotalSeconds, $health)
        break
      }
      if ($started.HasExited) { break }
      Start-Sleep -Milliseconds 500
    }
  }
  if (-not $served) {
    Say '새 앱이 응답하지 않아 되돌린다'
    if ($started -and -not $started.HasExited) { Stop-Tree $started }
    Undo-Swap
    $null = Open-App
    exit 1
  }
  Remove-Retry $old
  Say '바꿨다'
} catch {
  Say ('멈췄다: ' + $_.Exception.Message)
  if ($waited -and -not $script:opened) {
    if (-not [IO.File]::Exists($app) -and [IO.File]::Exists($old)) { $null = Move-Retry $old $app }
    $null = Open-App
  }
  exit 1
} finally {
  Remove-Retry $ready
}
"""
POWERSHELL = Path(os.environ.get("SystemRoot") or r"C:\Windows") / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP, CREATE_BREAKAWAY_FROM_JOB, CREATE_NO_WINDOW = 0x8, 0x200, 0x1000000, 0x8000000


class Refused(Exception):
    """화면에 그대로 보여 줄 거절."""


def parse(tag) -> tuple[int, int, int] | None:
    """v0.1.1, 0.1.1 → (0, 1, 1). 미리 보기 꼴(v0.2.0-beta.1)과 그 밖은 None."""
    found = re.fullmatch(r"v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})", str(tag or "").strip())
    return tuple(int(n) for n in found.groups()) if found else None


def asset_name() -> str | None:
    """이 기기에 맞는 릴리스 파일 이름. 없으면 None."""
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        return {"arm64": "AlgoBlock-macos-arm64.dmg", "x86_64": "AlgoBlock-macos-x86_64.dmg"}.get(machine)
    if os.name == "nt" and machine in ("amd64", "x86_64"):
        return WINDOWS_ASSET
    return None


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def current_app() -> Path | None:
    """바꿀 앱. 묶인 macOS 앱이면 그 .app 경로(…/AlgoBlock.app/Contents/MacOS/AlgoBlock에서 셋 위), 묶인 Windows 앱이면 그 exe."""
    if os.name == "nt":  # resolve()는 연결한 네트워크 드라이브를 UNC 꼴로 바꿀 수 있어 쓰지 않는다
        exe = Path(os.path.abspath(sys.executable))
        return exe if frozen() and exe.suffix.lower() == ".exe" else None
    exe = Path(sys.executable).resolve()
    app = exe.parents[2] if len(exe.parents) > 2 else None
    return app if sys.platform == "darwin" and frozen() and app and app.suffix == ".app" and exe.parent.name == "MacOS" else None


def writable(app: Path) -> bool:
    """앱과 그 폴더에 쓸 수 있는가(관리자만 쓰는 곳, 붙인 dmg, 격리된 위치에서 연 앱은 아니다).
    Windows의 os.access는 읽기 전용 속성만 보고 권한(ACL)은 보지 않아, 그 폴더에 파일을 하나 만들어 본다(Program Files 등)."""
    if not (os.access(app.parent, os.W_OK) and os.access(app, os.W_OK)):
        return False
    if os.name != "nt":
        return True
    try:
        with tempfile.TemporaryFile(dir=app.parent):
            return True
    except OSError:
        return False


def beside(app: Path, tag: str) -> Path:
    """지금 앱 옆의 숨긴 이름(.AlgoBlock.exe.new, .AlgoBlock.exe.old)."""
    return app.with_name(f".{app.name}.{tag}")


def pick(release, current: str | None = None, name: str | None = None) -> dict | None:
    """최신 릴리스 응답에서 지금보다 새 버전이면 {version, notes, asset, sums}. 초안·미리 보기·옛 버전·모르는 태그는 None.
    asset은 이 기기의 파일(없으면 None), sums는 SHA256SUMS 파일 주소(없으면 None)."""
    if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
        return None
    version, now = parse(release.get("tag_name")), parse(current or VERSION)  # 기본은 부를 때의 VERSION
    if version is None or now is None or version <= now:
        return None
    files = {raw.get("name"): raw for raw in release.get("assets") or [] if isinstance(raw, dict)
             and str(raw.get("browser_download_url") or "").startswith(DOWNLOADS)}
    raw = files.get(name) if name else None
    asset = None
    if raw and isinstance(raw.get("size"), int) and 0 < raw["size"] <= MAX_SIZE:
        asset = {"name": name, "url": raw["browser_download_url"], "size": raw["size"], "digest": str(raw.get("digest") or "")}
    notes = str(release.get("html_url") or "")
    return {"version": ".".join(map(str, version)), "notes": notes if notes.startswith(PAGES) else PAGES + "releases",
            "asset": asset, "sums": files[SUMS]["browser_download_url"] if SUMS in files else None}


def fetch(url: str, timeout: float = 15):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": f"AlgoBlock/{VERSION}"}),
                                  timeout=timeout)


def hashes_of(found: dict) -> list[str]:
    """받을 파일의 SHA-256: GitHub이 준 digest와 릴리스의 SHA256SUMS에 적힌 값(있는 것 모두). 하나도 없으면 받지 않는다."""
    asset, out = found["asset"], []
    if asset["digest"].startswith("sha256:"):
        out.append(asset["digest"][7:].lower())
    if found["sums"]:
        with fetch(found["sums"]) as response:
            text = response.read(65536).decode("utf-8", "replace")
        listed = [parts[0].lower() for parts in (line.split() for line in text.splitlines()) if len(parts) == 2 and parts[1].lstrip("*") == asset["name"]]
        if not listed:
            raise Refused("릴리스의 SHA256SUMS에 이 파일이 없어 받지 않았어요.")
        out += listed
    if not out or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in out):
        raise Refused("이 버전에는 파일이 맞는지 확인할 값(SHA-256)이 없어 받지 않았어요.")
    return out


def stored() -> dict:
    """설정 파일의 내용. 없거나 깨졌으면 빈 것. 있는데 읽지 못하면(잠김 등) OSError를 낸다(save가 그 위에 덮어쓰지 않게)."""
    try:
        with FILE_LOCK:
            saved = json.loads((DIR / "settings.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}
    return saved if isinstance(saved, dict) else {}


def settings(saved: dict | None = None) -> dict:
    """auto(자동 확인), skip(건너뛴 버전), checked(마지막으로 확인한 시각), release(그때 찾은 새 버전의 릴리스 요약. 없으면 None).
    saved를 주면 파일 대신 그것을 고른다. 읽지 못하면 기본값."""
    if saved is None:
        try:
            saved = stored()
        except OSError:
            saved = {}
    checked = saved.get("checked")
    return {"auto": saved.get("auto") is not False, "skip": str(saved.get("skip") or ""),
            "checked": float(checked) if isinstance(checked, (int, float)) and checked > 0 else 0.0,
            "release": saved["release"] if isinstance(saved.get("release"), dict) else None}


def save(**changes) -> None:
    """설정 파일을 바꾼다. 확인 스레드와 화면 요청이 함께 쓰므로 잠근다(Windows는 읽는 중인 파일을 바꿔 넣지 못한다)."""
    with FILE_LOCK:
        current = settings(stored())  # 있는데 읽지 못하면 여기서 멈춘다(기본값으로 덮어써 자동 확인 끔·건너뛴 버전을 잃지 않게)
        DIR.mkdir(parents=True, exist_ok=True)
        tmp = DIR / "settings.tmp"
        tmp.write_text(json.dumps({**current, **changes}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(DIR / "settings.json")


def view() -> dict:
    with LOCK:
        now = dict(NOW)
    app = current_app()
    latest = now["latest"]
    saved = settings()
    return {**now, "auto": saved["auto"], "skip": saved["skip"], "current": VERSION, "frozen": frozen(),
            "latest": latest and {"version": latest["version"], "notes": latest["notes"], "size": latest["asset"]["size"] if latest["asset"] else 0, "asset": bool(latest["asset"])},
            "installable": bool(app), "can_install": now["state"] == "ready" and bool(app) and writable(app)}


def unknown() -> None:
    """확인 실패를 알린다(LOCK을 잡고 부른다). 알던 새 버전이 있으면 다시 받을 수 있게 그대로 둔다."""
    if NOW["state"] not in ("available", "ready", "failed", *BUSY):
        NOW.update(state="unknown", message="새 버전을 확인하지 못했어요. 인터넷 연결을 확인하고 다시 해 보세요.")


def summary(release: dict) -> dict:
    """다음에 켤 때 다시 알리려고 저장하는 릴리스 요약. 되살릴 때 pick()으로 다시 검사한다."""
    keys = ("name", "size", "browser_download_url", "digest")
    return {"tag_name": release.get("tag_name"), "html_url": release.get("html_url"),
            "assets": [{key: raw.get(key) for key in keys} for raw in release.get("assets") or [] if isinstance(raw, dict)]}


def check() -> bool | None:
    """최신 릴리스를 본다. 확인했으면 True, 실패하면 False('unknown', 이미 알던 새 버전과 받은 파일은 그대로 둔다),
    받거나 바꾸는 중이라 건너뛰면 None. 확인하면 그 시각과 찾은 새 버전을 저장한다(껐다 켜도 24시간 안에는 다시 묻지 않는다)."""
    with LOCK:
        if NOW["state"] in BUSY:
            return None
    try:
        with fetch(LATEST, 10) as response:
            release = json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        release = {} if exc.code == 404 else None  # 404: 아직 릴리스가 없다
    except (OSError, ValueError):
        release = None
    found = pick(release, name=asset_name()) if release else None
    if release is not None:
        with contextlib.suppress(OSError):  # 저장하지 못해도 확인은 됐다(다음에 켤 때 다시 물을 뿐)
            save(checked=time.time(), release=summary(release) if found else None)
    with LOCK:
        if NOW["state"] in BUSY:
            return None
        if release is None:
            unknown()
            return False
        if not (NOW["state"] == "ready" and found and NOW["latest"]["version"] == found["version"]):
            NOW.update(state="available" if found else "latest", latest=found, progress=0, message="", file="")
        return True


def check_in_time(limit: float = LIMIT) -> bool | None:
    """시간 한도 안에 확인한다(이름 풀이처럼 소켓 시간 제한이 닿지 않는 곳에서 멈출 수 있다). 넘기면 실패로 친다.
    멈춘 확인은 뒤에 남아 끝나는 대로 결과만 남긴다. 앞의 확인이 아직 돌면 새로 띄우지 않고 그 결과를 같은 한도로 기다린다."""
    with LOCK:
        if CHECKING and CHECKING[-1][0].is_alive():
            worker, out = CHECKING[-1]
        else:
            out = []
            worker = threading.Thread(target=lambda: out.append(check()), daemon=True, name="update-check-once")
            CHECKING[:] = [(worker, out)]
            worker.start()
    worker.join(limit)
    if out:
        return out[0]
    with LOCK:
        unknown()
    return False


def first_due(now: float) -> float:
    """켤 때의 다음 확인 시각: 마지막 확인에서 24시간 뒤. 확인한 적이 없거나 시계가 뒤로 갔으면 지금."""
    checked = settings()["checked"]
    return checked + DAY if 0 < checked <= now else now


def record(ok: bool | None, now: float, auto: bool) -> None:
    """확인 결과로 다음 자동 확인 시각을 정한다. 성공하면 24시간 뒤(실패 수를 되돌린다),
    자동 확인이 실패하면 1시간에서 두 배씩 최대 6시간 뒤. '지금 확인'의 실패와 건너뜀(None)은 일정을 바꾸지 않는다."""
    with LOCK:
        if ok:
            PLAN.update(due=now + DAY, fails=0)
        elif ok is False and auto:
            PLAN.update(due=now + min(RETRY * 2 ** PLAN["fails"], RETRY_MAX), fails=min(PLAN["fails"] + 1, 8))


def tick(now: float) -> None:
    """때가 됐고 자동 확인이 켜져 있으면 확인한다(꺼 두었다 켜면 다음 tick에서 바로)."""
    with LOCK:
        if PLAN["due"] - now > DAY + RETRY_MAX:  # 도는 중에 시계가 크게 뒤로 갔다: 멀어진 날짜를 기다리지 않고 바로
            PLAN["due"] = now
        due = PLAN["due"]
    if now >= due and settings()["auto"]:
        record(check_in_time(), now, auto=True)


def restore() -> None:
    """지난번에 찾아 둔 새 버전을 다시 알린다(24시간 안에 다시 켜면 묻지 않으므로). pick()으로 다시 검사해 지금보다 새 것만."""
    release = settings()["release"]
    found = pick(release, name=asset_name()) if release else None
    with LOCK:
        if found and NOW["state"] == "idle":
            NOW.update(state="available", latest=found)


def download() -> None:
    with LOCK:
        latest = NOW["latest"]
        if NOW["state"] not in ("available", "failed") or not latest:
            raise Refused("받을 새 버전이 없어요.")
        if not frozen():
            raise Refused("소스에서 실행 중이라 여기서 업데이트하지 않아요. git으로 새 버전을 받아 주세요(git pull).")
        if not latest["asset"]:
            raise Refused("이 버전에는 이 기기에 맞는 설치 파일이 없어요.")
        NOW.update(state="downloading", progress=0, message="", file="")
    threading.Thread(target=fetch_file, args=(latest,), daemon=True, name="update-download").start()


def fetch_file(found: dict) -> None:
    """받으며 SHA-256을 센다. 크기나 해시가 다르면 지운다. 끝나면 'ready', 실패하면 'failed'(지금 앱은 그대로)."""
    asset, folder = found["asset"], DIR / found["version"]
    part = folder / (asset["name"] + ".part")
    try:
        expected = hashes_of(found)
        folder.mkdir(parents=True, exist_ok=True)
        digest, done = hashlib.sha256(), 0
        with fetch(asset["url"], 30) as response, open(part, "wb") as out:
            while chunk := response.read(1 << 20):
                done += len(chunk)
                if done > asset["size"]:
                    break
                digest.update(chunk)
                out.write(chunk)
                with LOCK:
                    NOW["progress"] = done * 100 // asset["size"]
        if done != asset["size"] or any(value != digest.hexdigest() for value in expected):
            raise Refused("받은 파일이 릴리스에 적힌 것과 달라 지웠어요. 설치하지 않았어요. 다시 받아 보세요.")
        part.replace(folder / asset["name"])
        with LOCK:
            NOW["sha256"] = digest.hexdigest()  # 설치 직전에 다시 견준다(받은 뒤 파일이 바뀌었으면 설치하지 않는다)
    except Refused as exc:
        return failed(str(exc), part)
    except Exception as exc:  # noqa: BLE001 - 무슨 일이든 '받는 중'에 멈춰 있지 않게 한다
        print(f"update download: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
        return failed("새 버전을 받지 못했어요. 인터넷 연결을 확인하고 다시 해 보세요. 지금 앱은 그대로예요.", part)
    app = current_app()
    with LOCK:
        NOW.update(state="ready", progress=100, file=str(folder / asset["name"]),
                   message="" if app and writable(app) else
                   "내려받았어요. 이 앱이 있는 곳에 쓸 수 없어 직접 바꿔야 해요. 앱을 끝낸 뒤 받은 파일로 바꿔 주세요." if app else
                   "내려받았어요. 앱을 끝낸 뒤 받은 파일로 바꿔 주세요.")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while chunk := handle.read(1 << 20):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def failed(message: str, part: Path | None = None) -> None:
    if part:
        part.unlink(missing_ok=True)
    with LOCK:
        NOW.update(state="failed", progress=0, message=message, file="")


def run(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True, timeout=600)


def put_beside(app: Path, dmg: Path, version: str) -> Path:
    """dmg를 읽기 전용으로 붙여 안의 앱이 이 앱의 그 버전인지 보고, 지금 앱 옆에 숨긴 이름으로 복사한다."""
    staged = app.with_name(f".{app.stem}-{version}.app")
    shutil.rmtree(staged, ignore_errors=True)
    mount = Path(tempfile.mkdtemp(prefix="mount-", dir=DIR))
    try:
        run(["hdiutil", "attach", "-nobrowse", "-readonly", "-noautoopen", "-mountpoint", str(mount), str(dmg)])
        source = mount / "AlgoBlock.app"
        info = plistlib.loads((source / "Contents" / "Info.plist").read_bytes())
        if info.get("CFBundleIdentifier") != BUNDLE_ID or info.get("CFBundleShortVersionString") != version:
            raise Refused("받은 파일 안의 앱이 이 앱의 새 버전이 아니에요. 설치하지 않았어요.")
        run(["ditto", str(source), str(staged)])
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    finally:
        if subprocess.run(["hdiutil", "detach", str(mount)], capture_output=True).returncode:
            subprocess.run(["hdiutil", "detach", "-force", str(mount)], capture_output=True)
        try:
            mount.rmdir()
        except OSError:
            pass
    # 우리 코드가 받은 파일에는 보통 격리 표시가 없다. 붙어 있으면 새 앱에서만 걷는다(서명이 없어 Gatekeeper가 막는다)
    if subprocess.run(["xattr", "-p", "com.apple.quarantine", str(staged)], capture_output=True).returncode == 0:
        run(["xattr", "-dr", "com.apple.quarantine", str(staged)])
    return staged


def swap_later(app: Path, staged: Path) -> None:
    """바꿔 끼우는 스크립트를 이 프로세스와 떼어 띄운다(앱이 끝나도 남는다)."""
    script = DIR / "swap.sh"
    script.write_text(SWAP_SH, encoding="utf-8")
    with open(DIR / "swap.log", "ab") as log:
        subprocess.Popen(["/bin/sh", str(script), str(os.getpid()), str(app), str(staged)],
                         stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def put_beside_exe(app: Path, exe: Path, want: str) -> Path:
    """받은 exe를 지금 exe 옆에 숨긴 이름으로 복사하고(같은 드라이브라 바꿔 끼우기는 이름 바꾸기 둘이다) 복사본의 해시를 다시 견준다.
    copyfile은 내용만 복사해 격리 표시(Zone.Identifier)가 따라오지 않는다. 그래도 붙어 있으면 새 파일에서만 걷는다."""
    staged = beside(app, "new")
    try:
        shutil.copyfile(exe, staged)
        if file_sha256(staged) != want:
            raise Refused("옆에 복사한 새 앱이 받은 파일과 달라요. 설치하지 않았어요. 다시 해 보세요.")
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    with contextlib.suppress(OSError):
        os.remove(f"{staged}:Zone.Identifier")
    return staged


def ps_text(value) -> str:
    """PowerShell의 작은따옴표 글. 안의 작은따옴표는 겹쳐 쓴다(PowerShell은 ‘ ’ ‚ ‛도 작은따옴표로 읽는다). $와 `는 그대로 글자다."""
    text = str(value)
    for quote in "'‘’‚‛":
        text = text.replace(quote, quote * 2)
    return f"'{text}'"


def ui_port() -> int:
    """앱의 로컬 서버 포트(server.py와 window.py가 같은 값을 읽는다). 새 앱은 같은 환경을 물려받아 같은 포트로 뜬다."""
    try:
        return int(os.environ.get("ALGOBLOCK_UI_PORT", "8791"))
    except ValueError:
        return 8791


def swap_ps1(app: Path, new: Path, pids: list[int], wait: int = 60, health: int = 90, port: int | None = None) -> str:
    """바꿔 끼우는 PowerShell 스크립트의 글. 값은 인자로 넘기지 않고 맨 위에 글로 박는다(따옴표 해석이 한 군데뿐이다).
    health: 새 앱의 로컬 서버가 응답하기를 기다리는 초(묶음을 풀고 모델을 불러오는 첫 실행은 느리다)."""
    values = {"app": ps_text(app), "new": ps_text(new), "old": ps_text(beside(app, "old")), "log": ps_text(DIR / "swap.log"),
              "ready": ps_text(DIR / "swap.waiting"), "ids": f"@({', '.join(str(int(pid)) for pid in pids)})",
              "wait": str(int(wait)), "health": str(int(health)), "url": ps_text(f"http://127.0.0.1:{int(port or ui_port())}/")}
    return "".join(f"${name} = {value}\n" for name, value in values.items()) + SWAP_PS1


def app_pids() -> list[int]:
    """끝나기를 기다릴 프로세스. onefile로 묶이면 풀어 놓는 부모 프로세스가 exe를 잡고 있다가 이 프로세스가 끝난 뒤 끝난다."""
    return [os.getpid(), os.getppid()] if frozen() and not inside(getattr(sys, "_MEIPASS", ""), os.path.dirname(sys.executable)) else [os.getpid()]


def inside(path: str, folder: str) -> bool:
    """path가 folder이거나 그 아래인가(대소문자·구분자는 이 OS의 규칙대로)."""
    path, folder = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
    return path == folder or path.startswith(folder.rstrip(os.sep) + os.sep)


def clean_env() -> dict:
    """새 앱이 이 앱의 풀어 놓은 폴더(이 앱이 끝나면 지워진다)를 가리키지 않고 새로 시작하게 한다:
    PyInstaller의 표시를 걷고, 값이 그 폴더 아래를 가리키는 변수는 이름과 상관없이 걷는다(런처가 넣는 ALGOBLOCK_UI_STATIC 등). PATH는 그 항목만 뺀다."""
    bundle = getattr(sys, "_MEIPASS", "")
    env = {}
    for key, value in os.environ.items():
        if key.upper().startswith(("_PYI", "_MEIPASS")) or (bundle and key.upper() != "PATH" and os.path.isabs(value) and inside(value, bundle)):
            continue
        env[key] = value
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    if bundle:
        path_key = next((key for key in env if key.upper() == "PATH"), "PATH")
        env[path_key] = os.pathsep.join(part for part in env.get(path_key, "").split(os.pathsep) if part and not inside(part, bundle))
    return env


def detached(args: list[str], out: Path, flags: int = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP) -> subprocess.Popen:
    """이 앱과 떼어 띄운다(보이지 않는 제 콘솔로, 앱이 끝나도 남게). 콘솔이 아예 없는 DETACHED_PROCESS는 PowerShell이 시작하지 못할 수 있어
    쓰지 않는다. PyInstaller가 바꾼 DLL 찾는 길은 띄우는 동안만 되돌린다(자식이 물려받는다)."""
    import ctypes

    kernel32 = ctypes.windll.kernel32
    saved = ctypes.create_unicode_buffer(32768)
    had = kernel32.GetDllDirectoryW(32768, saved)
    kernel32.SetDllDirectoryW(None)
    try:
        with open(out, "ab") as log:
            for breakaway in (CREATE_BREAKAWAY_FROM_JOB, 0):  # 작업 개체(Job) 안이면 벗어나 본다. 막혀 있으면 그대로 띄운다
                try:
                    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=clean_env(),
                                            creationflags=flags | breakaway)
                except OSError:
                    if not breakaway:
                        raise
    finally:
        kernel32.SetDllDirectoryW(saved.value if had else None)


def tail(path: Path, size: int = 3000) -> str:
    """기록 파일의 끝(진단용). 없으면 '(없음)'. PowerShell 5.1의 출력은 OEM 코드 페이지일 수 있어 깨진 글자는 바꿔 읽는다."""
    try:
        return path.read_bytes()[-size:].decode("utf-8", "replace")
    except OSError:
        return "(없음)"


def swap_later_exe(app: Path, staged: Path, pids: list[int] | None = None, wait: int = 60, health: int = 90, handshake: float = 20,
                   port: int | None = None) -> subprocess.Popen:
    """바꿔 끼우는 PowerShell 스크립트를 떼어 띄우고, 그 스크립트가 앱을 잡고 기다리기 시작한 것을 본 뒤에 그 프로세스를 돌려준다.
    띄우지 못하거나 handshake초 안에 기다리기 시작하지 않으면(실행 정책이 막는 등) 스크립트를 끝내고 옆에 둔 새 exe를 지운다. 앱은 그대로."""
    script, ready = DIR / "swap.ps1", DIR / "swap.waiting"
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        ready.unlink(missing_ok=True)
        script.write_text(swap_ps1(app, staged, app_pids() if pids is None else pids, wait, health, port), encoding="utf-8-sig")  # BOM: Windows PowerShell 5.1이 한글을 UTF-8로 읽게
        try:
            process = detached([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)], DIR / "swap-out.log")
        except OSError:
            raise Refused("바꾸는 도구(PowerShell)를 띄우지 못했어요. 지금 앱은 그대로예요. 앱을 끝낸 뒤 받은 파일로 직접 바꿀 수 있어요.") from None
        began = time.monotonic()
        while not ready.exists():
            if process.poll() is not None or time.monotonic() - began > handshake:
                with contextlib.suppress(OSError):
                    process.kill()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(5)  # 끝난 뒤에 출력 파일을 읽는다
                # 화면에는 짧은 거절만, 까닭(종료 코드, PowerShell의 출력, 스크립트의 첫 기록)은 표준 오류에 남긴다
                print(f"update swap: PowerShell이 기다리기 시작하지 않았다. 종료 코드 {process.returncode}, "
                      f"{time.monotonic() - began:.1f}초\n[swap-out.log]\n{tail(DIR / 'swap-out.log')}\n[swap.log]\n{tail(DIR / 'swap.log')}",
                      file=sys.stderr, flush=True)
                raise Refused("바꾸는 도구(PowerShell)가 시작하지 않았어요. 지금 앱은 그대로예요. 앱을 끝낸 뒤 받은 파일로 직접 바꿀 수 있어요.")
            time.sleep(0.1)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return process


def swapping_now() -> bool:
    """Windows의 바꾸는 스크립트가 아직 도는가(새 앱이 잘 켜지는지 보는 동안 옛 exe를 지우면 되돌릴 수 없다). 5분 지난 표시는 남은 찌꺼기로 본다."""
    try:
        return time.time() - (DIR / "swap.waiting").stat().st_mtime < 300
    except OSError:
        return False


def by_hand(ending: str) -> str:
    """직접 바꾸는 법(플랫폼마다). ending: '바꿔 주세요', '바꿀 수도 있어요' 같은 끝말."""
    if os.name == "nt":
        return f"앱을 끝낸 뒤 받은 exe로 지금 exe를 직접 {ending}"
    return f"내려받은 dmg를 열어 직접 {ending}"


def install(stop) -> None:
    app = current_app()
    with LOCK:
        if NOW["state"] != "ready" or not NOW["file"]:
            raise Refused("먼저 새 버전을 받아 주세요.")
        if not app:
            raise Refused("여기서는 바꿀 수 없어요. 앱을 끝낸 뒤 받은 파일로 바꿔 주세요.")
        if not writable(app):
            raise Refused(f"이 앱이 있는 곳에 쓸 수 없어요(관리자만 쓰는 폴더 등). {by_hand('바꿔 주세요')}: {NOW['file']}")
        file, version, want = Path(NOW["file"]), NOW["latest"]["version"], NOW.get("sha256")
        NOW.update(state="installing", message="")
    if not want or file_sha256(file) != want:  # 받을 때 견준 해시와 지금 파일이 다르면(받은 뒤 바뀜) 설치하지 않는다
        return failed("받은 파일이 받을 때와 달라져 지웠어요. 설치하지 않았어요. 다시 받아 보세요.", file)
    threading.Thread(target=replace_and_quit, args=(app, file, version, want, stop), daemon=True, name="update-install").start()


def replace_and_quit(app: Path, file: Path, version: str, want: str, stop) -> None:
    try:
        if os.name == "nt":
            swap_later_exe(app, put_beside_exe(app, file, want))
        else:
            swap_later(app, put_beside(app, file, version))
    except Refused as exc:
        return failed_install(str(exc))
    except Exception as exc:  # noqa: BLE001 - 무슨 일이든 '바꾸는 중'에 멈춰 있지 않게 한다
        print(f"update install: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
        return failed_install(f"새 버전으로 바꾸지 못했어요. 지금 앱은 그대로예요. {by_hand('바꿀 수도 있어요')}: {file}")
    with LOCK:
        NOW["state"] = "restarting"
    time.sleep(1)  # 화면이 '다시 켜는 중'을 받아 갈 틈
    quit_app(stop)


def failed_install(message: str) -> None:
    with LOCK:
        NOW.update(state="ready", message=message)  # 받은 파일은 남긴다(다시 해 보거나 직접 바꾼다)


def quit_app(stop) -> None:
    """돌고 있는 채점을 멈추고 창을 닫아 앱을 끝낸다(창이 없으면 서버만 끝낸다). 5초 안에 끝나지 않으면 프로세스를 끝낸다.
    쓰던 코드는 화면이 바꾸기를 부르기 전에 저장한다(app.js의 flushSaves)."""
    stop()
    webview = sys.modules.get("webview")
    try:
        for window in list(getattr(webview, "windows", None) or []):
            window.destroy()
    except Exception as exc:  # noqa: BLE001 - 창을 못 닫아도 아래에서 끝낸다
        print(f"update quit: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
    time.sleep(5)
    stop()
    os._exit(0)


def reveal() -> None:
    """받은 파일을 Finder·탐색기에서 보여 준다."""
    with LOCK:
        file = NOW["file"]
    if not file or not Path(file).is_file():
        raise Refused("받은 파일이 없어요.")
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", file], check=False)
    elif os.name == "nt":
        subprocess.run(["explorer", f"/select,{file}"], check=False)
    else:
        raise Refused(f"받은 파일: {file}")


def tidy() -> None:
    """지금 버전과 같거나 옛 버전의 받은 파일을 지운다(바꾸기가 끝난 것). Windows에서 바꾸고 남은 옛 exe와 덜 바꾼 새 exe도 지운다
    (바꾸는 스크립트가 아직 돌면 둔다. 새 앱이 켜지지 않으면 옛 exe로 되돌려야 한다)."""
    for folder in DIR.glob("*") if DIR.is_dir() else []:
        version = parse(folder.name)
        if folder.is_dir() and version and version <= parse(VERSION):
            shutil.rmtree(folder, ignore_errors=True)
    app = current_app()
    if app and not swapping_now():
        for leftover in (beside(app, "old"), beside(app, "new")):
            if leftover.is_file():
                with contextlib.suppress(OSError):
                    leftover.unlink()


def last_swap_note() -> str:
    """지난번 바꾸기의 기록(swap.log)을 한 번 읽고 swap.prev.log로 옮긴다. 바꾸지 못했거나 되돌렸으면 화면에 띄울 글.
    (Windows에서 되돌린 뒤 다시 연 옛 앱이 같은 업데이트를 말없이 다시 권하지 않게)"""
    log, prev = DIR / "swap.log", DIR / "swap.prev.log"
    if swapping_now():  # 바꾸는 스크립트가 아직 쓰는 중이다(새 앱이 켜진 때). 다음에 켤 때 끝난 기록을 읽는다
        return ""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
        log.replace(prev)
    except OSError:
        return ""
    if not any(word in text for word in ("되돌렸다", "되돌리지 못했다", "바꾸지 않았다", "멈췄다")):
        return ""
    return f"지난번 업데이트를 마치지 못해 지금 버전을 그대로 쓰고 있어요. 기록: {prev}"


def start() -> None:
    """뒤에서 확인 일정을 돌린다(설정에서 끄면 건너뛴다). 한 프로세스에 한 번만.
    켤 때: 마지막 확인에서 24시간이 지났으면 바로, 아니면 그때까지 기다린다(그동안은 지난번에 찾은 새 버전을 다시 알린다)."""
    if STARTED:
        return
    STARTED.append(True)
    tidy()
    restore()
    note = last_swap_note()
    with LOCK:
        PLAN["due"] = first_due(time.time())
        if note:
            NOW["message"] = note

    def loop():
        while True:
            try:
                tick(time.time())
            except Exception as exc:  # noqa: BLE001 - 일정이 멈추면 다시는 확인하지 않는다
                print(f"update tick: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
            time.sleep(TICK)

    threading.Thread(target=loop, daemon=True, name="update-check").start()


def handle(body: dict, stop) -> dict:
    """/api/update. action: status(지금 상태), check(지금 확인), auto(자동 확인 켜고 끄기, on), skip(이 버전 건너뛰기),
    download(받기), install(바꾸고 다시 켜기, 묶인 macOS·Windows 앱), reveal(받은 파일 보기)."""
    action = body.get("action")
    if action == "check":  # 일정과 상관없이 바로 묻는다. 성공하면 다음 자동 확인은 24시간 뒤
        record(check_in_time(), time.time(), auto=False)
    elif action == "auto":
        save(auto=body.get("on") is True)
    elif action == "skip":
        with LOCK:
            latest = NOW["latest"]
        if latest:
            save(skip=latest["version"])
    elif action == "download":
        download()
    elif action == "install":
        install(stop)
    elif action == "reveal":
        reveal()
    elif action != "status":
        raise Refused("알 수 없는 요청이에요.")
    return view()
