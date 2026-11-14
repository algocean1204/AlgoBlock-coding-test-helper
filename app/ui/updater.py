"""새 버전 확인과 업데이트. 표준 라이브러리만 쓴다.

흐름: 확인(GitHub의 최신 릴리스) → 알림(화면 위쪽 막대) → 받기 → 무결성 확인(SHA-256) → 바꾸기 → 다시 켜기.
- 확인: 서버가 뜰 때 한 번, 그 뒤 6시간마다(설정에서 끌 수 있다). 실패는 조용히 넘긴다.
- 받기와 바꾸기는 묶인 앱(PyInstaller)에서만 한다. 소스에서 실행하면 확인만 한다(git으로 받는다).
- macOS: dmg를 읽기 전용으로 붙여 새 .app을 지금 앱 옆에 복사하고, 앱이 끝난 뒤 작은 셸 스크립트가 바꿔 끼우고 다시 연다.
- Windows: 받아서 파일 위치를 여는 데까지만 한다(바꾸기는 사용자가 한다).
- 받은 파일은 자료 폴더의 updates/<버전>/에 둔다. 릴리스에 적힌 해시와 다르면 지우고 설치하지 않는다.
"""

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

VERSION = "0.1.0"  # 앱의 버전은 여기 한 곳에 둔다(algoblock.spec과 build_mac.sh가 이 줄을 읽는다)
REPO = "algocean1204/AlgoBlock-coding-test-helper"
LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOADS = f"https://github.com/{REPO}/releases/download/"  # 받는 주소는 이 저장소의 릴리스 파일만
PAGES = f"https://github.com/{REPO}/"
SUMS = "SHA256SUMS"
BUNDLE_ID = "io.github.algocean1204.algoblock"
EVERY = 6 * 60 * 60
MAX_SIZE = 2 * 1024 ** 3
DIR = Path(tempfile.gettempdir()) / "algoblock-updates"  # 서버가 자료 폴더 아래(updates)로 바꾼다
BUSY = ("downloading", "installing", "restarting")

LOCK = threading.Lock()
NOW = {"state": "idle", "latest": None, "progress": 0, "message": "", "file": ""}
STARTED = []

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
        return "AlgoBlock-windows-x64.exe"
    return None


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def current_app() -> Path | None:
    """묶인 macOS 앱이면 그 .app 경로(…/AlgoBlock.app/Contents/MacOS/AlgoBlock에서 셋 위)."""
    exe = Path(sys.executable).resolve()
    app = exe.parents[2] if len(exe.parents) > 2 else None
    return app if sys.platform == "darwin" and frozen() and app and app.suffix == ".app" and exe.parent.name == "MacOS" else None


def writable(app: Path) -> bool:
    """앱과 그 폴더에 쓸 수 있는가(관리자만 쓰는 곳, 붙인 dmg, 격리된 위치에서 연 앱은 아니다)."""
    return os.access(app.parent, os.W_OK) and os.access(app, os.W_OK)


def pick(release, current: str = VERSION, name: str | None = None) -> dict | None:
    """최신 릴리스 응답에서 지금보다 새 버전이면 {version, notes, asset, sums}. 초안·미리 보기·옛 버전·모르는 태그는 None.
    asset은 이 기기의 파일(없으면 None), sums는 SHA256SUMS 파일 주소(없으면 None)."""
    if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
        return None
    version, now = parse(release.get("tag_name")), parse(current)
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


def settings() -> dict:
    try:
        saved = json.loads((DIR / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    saved = saved if isinstance(saved, dict) else {}
    return {"auto": saved.get("auto") is not False, "skip": str(saved.get("skip") or "")}


def save(**changes) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = DIR / "settings.tmp"
    tmp.write_text(json.dumps({**settings(), **changes}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DIR / "settings.json")


def view() -> dict:
    with LOCK:
        now = dict(NOW)
    app = current_app()
    latest = now["latest"]
    return {**now, **settings(), "current": VERSION, "frozen": frozen(),
            "latest": latest and {"version": latest["version"], "notes": latest["notes"], "size": latest["asset"]["size"] if latest["asset"] else 0, "asset": bool(latest["asset"])},
            "installable": bool(app), "can_install": now["state"] == "ready" and bool(app) and writable(app)}


def check() -> None:
    """최신 릴리스를 본다. 실패하면 'unknown'(이미 알던 새 버전과 받은 파일은 그대로 둔다)."""
    with LOCK:
        if NOW["state"] in BUSY:
            return
    try:
        with fetch(LATEST, 10) as response:
            release = json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        release = {} if exc.code == 404 else None  # 404: 아직 릴리스가 없다
    except (OSError, ValueError):
        release = None
    found = pick(release, name=asset_name()) if release else None
    with LOCK:
        if NOW["state"] in BUSY or (NOW["state"] == "ready" and found and NOW["latest"]["version"] == found["version"]):
            return
        if release is None:
            if NOW["state"] not in ("available", "ready", "failed"):  # 알던 새 버전으로 다시 받을 수 있게 둔다
                NOW.update(state="unknown", message="새 버전을 확인하지 못했어요. 인터넷 연결을 확인하고 다시 해 보세요.")
            return
        NOW.update(state="available" if found else "latest", latest=found, progress=0, message="", file="")


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


def install(stop) -> None:
    app = current_app()
    with LOCK:
        if NOW["state"] != "ready" or not NOW["file"]:
            raise Refused("먼저 새 버전을 받아 주세요.")
        if not app:
            raise Refused("여기서는 바꿀 수 없어요. 앱을 끝낸 뒤 받은 파일로 바꿔 주세요.")
        if not writable(app):
            raise Refused(f"이 앱이 있는 곳에 쓸 수 없어요. 내려받은 dmg를 열어 직접 바꿔 주세요: {NOW['file']}")
        dmg, version, want = Path(NOW["file"]), NOW["latest"]["version"], NOW.get("sha256")
        NOW.update(state="installing", message="")
    if not want or file_sha256(dmg) != want:  # 받을 때 견준 해시와 지금 파일이 다르면(받은 뒤 바뀜) 설치하지 않는다
        return failed("받은 파일이 받을 때와 달라져 지웠어요. 설치하지 않았어요. 다시 받아 보세요.", dmg)
    threading.Thread(target=replace_and_quit, args=(app, dmg, version, stop), daemon=True, name="update-install").start()


def replace_and_quit(app: Path, dmg: Path, version: str, stop) -> None:
    try:
        swap_later(app, put_beside(app, dmg, version))
    except Refused as exc:
        return failed_install(str(exc))
    except Exception as exc:  # noqa: BLE001 - 무슨 일이든 '바꾸는 중'에 멈춰 있지 않게 한다
        print(f"update install: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
        return failed_install("새 버전으로 바꾸지 못했어요. 지금 앱은 그대로예요. 내려받은 dmg를 열어 직접 바꿀 수도 있어요.")
    with LOCK:
        NOW["state"] = "restarting"
    time.sleep(1)  # 화면이 '다시 켜는 중'을 받아 갈 틈
    quit_app(stop)


def failed_install(message: str) -> None:
    with LOCK:
        NOW.update(state="ready", message=message)  # 받은 파일은 남긴다(다시 해 보거나 직접 바꾼다)


def quit_app(stop) -> None:
    """창을 닫아 앱을 끝낸다(창이 없으면 서버만 끝낸다). 5초 안에 끝나지 않으면 채점을 멈추고 프로세스를 끝낸다."""
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
    """지금 버전과 같거나 옛 버전의 받은 파일을 지운다(바꾸기가 끝난 것)."""
    for folder in DIR.glob("*") if DIR.is_dir() else []:
        version = parse(folder.name)
        if folder.is_dir() and version and version <= parse(VERSION):
            shutil.rmtree(folder, ignore_errors=True)


def start() -> None:
    """뒤에서 켤 때 한 번, 그 뒤 6시간마다 확인한다(설정에서 끄면 건너뛴다). 한 프로세스에 한 번만."""
    if STARTED:
        return
    STARTED.append(True)
    tidy()

    def loop():
        while True:
            if settings()["auto"]:
                check()
            time.sleep(EVERY)

    threading.Thread(target=loop, daemon=True, name="update-check").start()


def handle(body: dict, stop) -> dict:
    """/api/update. action: status(지금 상태), check(지금 확인), auto(자동 확인 켜고 끄기, on), skip(이 버전 건너뛰기),
    download(받기), install(바꾸고 다시 켜기, macOS 묶인 앱), reveal(받은 파일 보기)."""
    action = body.get("action")
    if action == "check":
        check()
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
