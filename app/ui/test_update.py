"""업데이트 확인(updater.py). 네트워크와 시계는 가짜로 바꾼다. 바꿔 끼우기는 임시 폴더의 가짜 앱 둘로 스크립트를 돌려 본다
(macOS·Linux는 셸 스크립트, Windows는 PowerShell 스크립트. 각자 그 기기에서만 돈다. 스크립트 글을 만드는 부분은 어디서나 본다).

실행: cd app && python3 -B ui/test_update.py     (test_server.py도 이것을 부른다)
"""

import contextlib
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import updater  # noqa: E402

BASE = updater.DOWNLOADS + "v0.1.1/"
DMG = "AlgoBlock-macos-arm64.dmg"


def release(tag="v0.1.1", **extra) -> dict:
    return {"tag_name": tag, "draft": False, "prerelease": False, "html_url": updater.PAGES + "releases/tag/" + tag,
            "assets": [{"name": DMG, "size": 4, "browser_download_url": BASE + DMG, "digest": ""},
                       {"name": updater.SUMS, "size": 90, "browser_download_url": BASE + updater.SUMS}], **extra}


def fake_net(pages: dict):
    """주소 → 바이트(또는 예외)."""
    def fetch(url, timeout=15):
        page = pages[url]
        if isinstance(page, Exception):
            raise page
        return io.BytesIO(page)
    return patch.object(updater, "fetch", fetch)


def reset(folder: Path) -> None:
    updater.DIR = folder
    updater.NOW.update(state="idle", latest=None, progress=0, message="", file="")


def versions() -> None:
    assert updater.parse("v0.1.1") == (0, 1, 1) and updater.parse("0.10.0") > updater.parse("v0.9.9")
    for tag in ("v0.2.0-beta.1", "latest", "", None, "v1.2"):
        assert updater.parse(tag) is None, tag


def picking() -> None:
    found = updater.pick(release(), "0.1.0", DMG)
    assert found["version"] == "0.1.1" and found["asset"]["url"] == BASE + DMG and found["sums"] == BASE + updater.SUMS, found
    assert updater.pick(release(draft=True), "0.1.0", DMG) is None
    assert updater.pick(release(prerelease=True), "0.1.0", DMG) is None
    assert updater.pick(release("v0.2.0-rc.1"), "0.1.0", DMG) is None  # 미리 보기 꼴의 태그
    assert updater.pick(release("v0.1.0"), "0.1.0", DMG) is None and updater.pick(release("v0.0.9"), "0.1.0", DMG) is None
    assert updater.pick(release(), "0.1.0", "AlgoBlock-windows-x64.exe")["asset"] is None  # 이 기기의 파일이 없다(알림은 한다)
    assert updater.pick(release(assets=[]), "0.1.0", DMG)["asset"] is None
    elsewhere = release(assets=[{"name": DMG, "size": 4, "browser_download_url": "https://example.com/" + DMG}], html_url="https://example.com/x")
    found = updater.pick(elsewhere, "0.1.0", DMG)
    assert found["asset"] is None and found["notes"] == updater.PAGES + "releases"  # 다른 곳의 주소는 받지도 잇지도 않는다
    assert updater.pick("not json", "0.1.0", DMG) is None


def hashes() -> None:
    good = hashlib.sha256(b"data").hexdigest()
    found = updater.pick(release(), "0.1.0", DMG)
    with fake_net({BASE + updater.SUMS: f"{good}  {DMG}\n{'0' * 64}  other.exe\n".encode()}):
        assert updater.hashes_of(found) == [good]
    found["asset"]["digest"] = "sha256:" + good
    with fake_net({BASE + updater.SUMS: f"{good} *{DMG}\n".encode()}):
        assert updater.hashes_of(found) == [good, good]  # 둘 다 있으면 둘 다 견준다
    for sums in (b"", f"{good}  other.dmg\n".encode()):  # SHA256SUMS에 이 파일이 없다
        with fake_net({BASE + updater.SUMS: sums}):
            try:
                updater.hashes_of(found)
                raise AssertionError("SHA256SUMS에 없는 파일은 받지 않는다")
            except updater.Refused:
                pass
    found = updater.pick(release(assets=release()["assets"][:1]), "0.1.0", DMG)
    try:
        updater.hashes_of(found)
        raise AssertionError("견줄 해시가 없으면 받지 않는다")
    except updater.Refused as exc:
        assert "SHA-256" in str(exc)


def checking(folder: Path) -> None:
    reset(folder)
    with fake_net({updater.LATEST: OSError("오프라인")}):
        updater.check()
    assert updater.NOW["state"] == "unknown" and updater.NOW["latest"] is None
    with fake_net({updater.LATEST: urllib.error.HTTPError(updater.LATEST, 404, "Not Found", {}, None)}):
        updater.check()
    assert updater.NOW["state"] == "latest"  # 아직 릴리스가 없다
    with fake_net({updater.LATEST: json.dumps(release()).encode()}), patch.object(updater, "asset_name", lambda: DMG):
        updater.check()
    assert updater.NOW["state"] == "available" and updater.NOW["latest"]["version"] == "0.1.1"
    with fake_net({updater.LATEST: OSError("오프라인")}):
        updater.check()
    assert updater.NOW["state"] == "available"  # 확인이 실패해도 알던 새 버전은 그대로
    view = updater.handle({"action": "skip"}, lambda: None)
    assert view["skip"] == "0.1.1" and updater.settings()["skip"] == "0.1.1"
    assert updater.handle({"action": "auto", "on": False}, lambda: None)["auto"] is False
    try:
        updater.handle({"action": "rm"}, lambda: None)
        raise AssertionError("모르는 action은 거절한다")
    except updater.Refused:
        pass


def dev_build(folder: Path) -> None:
    """개발용 앱은 업데이트를 확인하지도 받지도 않는다(배포판이 덮어쓰지 않게). 실행기는 묶음 안의 flavor 파일로 개발용 빌드를 안다."""
    reset(folder)
    updater.NOW.update(state="available", latest=updater.pick(release(), "0.1.0", DMG))
    started = list(updater.STARTED)
    updater.STARTED.clear()
    try:
        with patch.dict(os.environ, {"ALGOBLOCK_FLAVOR": "dev"}), patch.object(updater, "frozen", lambda: True):
            updater.start()
            assert updater.STARTED == []  # 뒤에서 도는 확인을 띄우지 않았다
            try:
                updater.download()
                raise AssertionError("개발용 앱은 받지 않는다")
            except updater.Refused as exc:
                assert "개발용" in str(exc)
            with fake_net({}):  # '지금 확인'도 묻지 않는다(새 버전 안내를 띄우지 않게)
                try:
                    updater.handle({"action": "check"}, lambda: None)
                    raise AssertionError("개발용 앱은 확인하지 않는다")
                except updater.Refused as exc:
                    assert "개발용" in str(exc)
        assert updater.NOW["state"] == "available"
    finally:
        updater.STARTED[:] = started
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packaging"))
    import launcher

    folder.mkdir(parents=True, exist_ok=True)
    assert launcher.flavor(folder) == ""
    (folder / "flavor").write_text("dev\n", encoding="utf-8")
    assert launcher.flavor(folder) == "dev"


def downloading(folder: Path) -> None:
    reset(folder)
    updater.NOW.update(state="available", latest=updater.pick(release(), "0.1.0", DMG))
    try:
        updater.download()
        raise AssertionError("소스에서 실행하면 받지 않는다")
    except updater.Refused as exc:
        assert "git" in str(exc)
    assert updater.NOW["state"] == "available"

    good = hashlib.sha256(b"data").hexdigest()
    for body, sums, state in ((b"data", good, "ready"), (b"evil", good, "failed"), (b"data!", good, "failed"), (b"dat", good, "failed")):
        reset(folder / state / body.decode())
        found = updater.pick(release(), "0.1.0", DMG)
        updater.NOW.update(state="downloading", latest=found)
        with fake_net({BASE + updater.SUMS: f"{sums}  {DMG}\n".encode(), BASE + DMG: body}):
            updater.fetch_file(found)
        target = updater.DIR / "0.1.1" / DMG
        assert updater.NOW["state"] == state, (body, updater.NOW)
        assert target.is_file() == (state == "ready") and not (updater.DIR / "0.1.1" / (DMG + ".part")).exists()
        if state == "failed":
            assert "설치하지 않았어요" in updater.NOW["message"] and updater.NOW["file"] == ""  # 해시나 크기가 다르면 지우고 설치하지 않는다
        else:
            assert updater.NOW["file"] == str(target)
    with patch.object(sys, "frozen", True, create=True):
        reset(folder / "offline")
        found = updater.pick(release(), "0.1.0", DMG)
        updater.NOW.update(state="available", latest=found)
        with fake_net({BASE + updater.SUMS: OSError("오프라인")}), contextlib.redirect_stderr(io.StringIO()):
            updater.download()
            for _ in range(100):
                if updater.NOW["state"] != "downloading":
                    break
                time.sleep(0.02)
        assert updater.NOW["state"] == "failed" and "그대로" in updater.NOW["message"]


def installing(folder: Path) -> None:
    reset(folder)
    try:
        updater.install(lambda: None)
        raise AssertionError("받기 전에는 바꾸지 않는다")
    except updater.Refused:
        pass
    updater.NOW.update(state="ready", latest=updater.pick(release(), "0.1.0", DMG), file=str(folder / DMG))
    try:
        updater.install(lambda: None)
        raise AssertionError("묶인 macOS 앱이 아니면(소스 실행) 바꾸지 않는다")
    except updater.Refused:
        pass
    locked = folder / "locked"
    app = locked / "AlgoBlock.app"
    app.mkdir(parents=True)
    locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        # 관리자 권한으로 돌거나 Windows면(폴더의 읽기 전용 속성은 쓰기를 막지 않는다) 권한 비트가 막지 못한다
        if not os.access(locked, os.W_OK):
            with patch.object(updater, "current_app", lambda: app):
                assert updater.view()["can_install"] is False
                try:
                    updater.install(lambda: None)
                    raise AssertionError("쓸 수 없는 곳의 앱은 바꾸지 않는다")
                except updater.Refused as exc:
                    assert "직접 바꿔 주세요" in str(exc) and str(folder / DMG) in str(exc) and ("exe" if os.name == "nt" else "dmg를 열어") in str(exc)
            assert updater.NOW["state"] == "ready"
    finally:
        locked.chmod(stat.S_IRWXU)
    # 받을 때 견준 해시와 지금 파일이 다르면(받은 뒤 바뀜) 설치하지 않는다
    writable_dir = folder / "free"
    app = writable_dir / "AlgoBlock.app"
    app.mkdir(parents=True)
    dmg = folder / "changed.dmg"
    dmg.write_bytes(b"after")
    updater.NOW.update(state="ready", latest=updater.pick(release(), "0.1.0", DMG), file=str(dmg), sha256=hashlib.sha256(b"before").hexdigest())
    with patch.object(updater, "current_app", lambda: app), patch.object(updater, "replace_and_quit", lambda *a: (_ for _ in ()).throw(AssertionError("바뀐 파일로 설치하려 했다"))):
        updater.install(lambda: None)
    assert updater.NOW["state"] == "failed" and "달라져" in updater.NOW["message"] and not dmg.exists()


def swapping(folder: Path) -> None:
    """셸 스크립트: 앱이 끝나기를 기다렸다가 바꿔 끼우고 다시 연다. 새 앱을 넣지 못하면 옛 앱을 되돌린다."""
    bin_dir = folder / "bin"
    bin_dir.mkdir(parents=True)
    opened = folder / "opened.txt"
    (bin_dir / "open").write_text(f'#!/bin/sh\necho "$1" >> "{opened}"\n', encoding="utf-8")
    (bin_dir / "open").chmod(0o755)
    script = folder / "swap.sh"
    script.write_text(updater.SWAP_SH, encoding="utf-8")
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}

    def make(path: Path, mark: str) -> Path:
        (path / "Contents").mkdir(parents=True)
        (path / "Contents" / "mark").write_text(mark, encoding="utf-8")
        return path

    def run(app: Path, new: Path) -> str:
        alive = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.5)"])
        threading.Thread(target=alive.wait, daemon=True).start()  # 끝나면 거둬 들인다(좀비가 남으면 kill -0이 참이다)
        began = time.monotonic()
        out = subprocess.run(["/bin/sh", str(script), str(alive.pid), str(app), str(new)], env=env, capture_output=True, text=True, timeout=30)
        assert time.monotonic() - began >= 0.4, "앱이 끝나기 전에 바꾸면 안 된다"
        return out.stdout

    app = make(folder / "ok" / "AlgoBlock.app", "old")
    new = make(folder / "ok" / ".AlgoBlock-0.1.1.app", "new")
    assert "바꿨다" in run(app, new)
    assert (app / "Contents" / "mark").read_text(encoding="utf-8") == "new" and not new.exists()
    assert sorted(path.name for path in app.parent.iterdir()) == ["AlgoBlock.app"]  # 옛 앱을 남기지 않는다
    app = make(folder / "bad" / "AlgoBlock.app", "old")
    assert "되돌렸다" in run(app, folder / "bad" / ".AlgoBlock-없음.app")
    assert (app / "Contents" / "mark").read_text(encoding="utf-8") == "old"
    assert sorted(path.name for path in app.parent.iterdir()) == ["AlgoBlock.app"]
    assert opened.read_text(encoding="utf-8").split("\n")[:2] == [str(folder / "ok" / "AlgoBlock.app"), str(app)]  # 어느 쪽이든 앱을 다시 연다


def tidying(folder: Path) -> None:
    reset(folder)
    for name in ("0.0.9", "0.1.0", "0.1.1"):
        (folder / name).mkdir(parents=True)
    updater.save(auto=True)
    updater.tidy()
    assert sorted(path.name for path in folder.iterdir()) == ["0.1.1", "settings.json"]  # 바꾸기가 끝난 버전의 파일만 지운다
    # Windows에서 바꾸고 남은 옛 exe와 덜 바꾼 새 exe: 바꾸는 스크립트가 도는 동안은 두고(되돌릴 때 쓴다), 끝났으면 지운다
    place = folder / "앱 폴더"
    place.mkdir()
    exe = place / "AlgoBlock.exe"
    exe.write_bytes(b"app")
    for tag in ("old", "new"):
        updater.beside(exe, tag).write_bytes(tag.encode())
    (folder / "swap.waiting").write_text("waiting", encoding="utf-8")
    with patch.object(updater, "current_app", lambda: exe):
        updater.tidy()
        assert sorted(path.name for path in place.iterdir()) == [".AlgoBlock.exe.new", ".AlgoBlock.exe.old", "AlgoBlock.exe"]
        old = time.time() - 600
        os.utime(folder / "swap.waiting", (old, old))  # 5분 넘게 남은 표시는 찌꺼기다
        updater.tidy()
        assert sorted(path.name for path in place.iterdir()) == ["AlgoBlock.exe"]


def scheduling(folder: Path) -> None:
    """확인 일정(시계는 가짜): 켤 때 바로 → 24시간마다. 실패하면 1·2·4·6·6시간 뒤에 다시, 성공하면 24시간으로 돌아간다."""
    reset(folder)
    results, calls = [], []

    def fake_check():
        calls.append(True)
        return results.pop(0)

    hour, day = 3600, 24 * 3600
    with patch.object(updater, "check", fake_check):
        start = 1_000_000.0
        updater.PLAN.update(due=updater.first_due(start), fails=0)
        assert updater.PLAN["due"] == start  # 확인한 적이 없으면 켤 때 바로
        now = start
        for wait in (1, 2, 4, 6, 6):  # 실패할 때마다 두 배, 6시간에서 멈춘다
            results.append(False)
            updater.tick(now)
            assert updater.PLAN["due"] == now + wait * hour, (wait, updater.PLAN)
            updater.tick(now + wait * hour - 1)  # 때가 되기 전에는 묻지 않는다
            now += wait * hour
        assert len(calls) == 5
        results.append(True)
        updater.tick(now)
        assert updater.PLAN == {"due": now + day, "fails": 0}  # 성공하면 24시간 뒤, 실패 수는 되돌린다
        results.append(False)
        updater.tick(now + day)
        assert updater.PLAN["due"] == now + day + hour  # 다시 1시간부터
        results.append(None)  # 받거나 바꾸는 중이라 건너뛰었다: 일정은 그대로, 다음 tick에서 다시 본다
        updater.tick(now + day + hour)
        assert updater.PLAN["due"] == now + day + hour and updater.PLAN["fails"] == 1
        # 자동 확인을 끄면 때가 지나도 묻지 않는다
        updater.save(auto=False)
        before = len(calls)
        updater.tick(now + 10 * day)
        assert len(calls) == before
        updater.save(auto=True)
        # '지금 확인'은 일정과 상관없이 바로 묻는다. 실패해도 일정은 그대로, 성공하면 24시간 뒤로
        updater.PLAN.update(due=now + 100 * day, fails=3)
        results.append(False)
        updater.handle({"action": "check"}, lambda: None)
        assert len(calls) == before + 1 and updater.PLAN == {"due": now + 100 * day, "fails": 3}
        results.append(True)
        updater.handle({"action": "check"}, lambda: None)
        assert len(calls) == before + 2 and updater.PLAN["fails"] == 0 and abs(updater.PLAN["due"] - (time.time() + day)) < 60
    # 마지막 확인 시각을 저장해 두므로, 24시간 안에 다시 켜면 묻지 않는다
    updater.save(checked=start)
    assert updater.first_due(start + hour) == start + day and updater.first_due(start + 2 * day) == start + day
    assert updater.first_due(start - hour) == start - hour  # 시계가 뒤로 갔으면 바로 묻는다
    updater.save(checked="이상한 값")
    assert updater.first_due(start) == start


def remembering(folder: Path) -> None:
    """확인하면 그 시각과 찾은 새 버전을 저장한다. 다시 켜면(24시간 안이라 묻지 않아도) 그 새 버전을 다시 알린다."""
    reset(folder)
    before = time.time()
    with fake_net({updater.LATEST: json.dumps(release()).encode()}), patch.object(updater, "asset_name", lambda: DMG):
        assert updater.check() is True
    saved = updater.settings()
    assert saved["checked"] >= before and saved["release"]["tag_name"] == "v0.1.1"
    reset(folder)
    with patch.object(updater, "asset_name", lambda: DMG):
        updater.restore()
    assert updater.NOW["state"] == "available" and updater.NOW["latest"]["asset"]["url"] == BASE + DMG
    # 저장된 요약도 pick()으로 다시 검사한다: 다른 곳의 주소는 받지 않고, 지금보다 새 버전이 아니면 알리지 않는다
    updater.save(release={**release(), "assets": [{"name": DMG, "size": 4, "browser_download_url": "https://example.com/" + DMG}]})
    reset(folder)
    with patch.object(updater, "asset_name", lambda: DMG):
        updater.restore()
    assert updater.NOW["latest"]["asset"] is None
    updater.save(release=release("v0.1.0"))
    reset(folder)
    updater.restore()
    assert updater.NOW["state"] == "idle"
    with fake_net({updater.LATEST: OSError("오프라인")}):
        assert updater.check() is False
    with fake_net({updater.LATEST: json.dumps(release("v0.1.0")).encode()}):
        assert updater.check() is True
    assert updater.NOW["state"] == "latest" and updater.settings()["release"] is None  # 새 버전이 없으면 지운다
    updater.NOW["state"] = "downloading"
    assert updater.check() is None  # 받는 중에는 묻지 않는다
    updater.NOW["state"] = "idle"


def stalling(folder: Path) -> None:
    """확인이 시간 한도를 넘기면 실패로 친다. 앞의 확인이 아직 돌면 새로 띄우지 않고 그 결과를 기다린다."""
    reset(folder)
    gate, calls = threading.Event(), []

    def slow():
        calls.append(True)
        return gate.wait(5) and True

    with patch.object(updater, "check", slow):
        began = time.monotonic()
        assert updater.check_in_time(0.2) is False and time.monotonic() - began < 2
        assert updater.NOW["state"] == "unknown"
        assert updater.check_in_time(0.2) is False and len(calls) == 1  # 앞의 확인이 아직 멈춰 있다: 새로 띄우지 않는다
        threading.Timer(0.2, gate.set).start()  # 자동 확인이 도는 중에 '지금 확인'을 누르면 그 결과를 받는다
        assert updater.check_in_time(5) is True and len(calls) == 1
        assert updater.check_in_time(1) is True and len(calls) == 2


def staging(folder: Path) -> None:
    """Windows의 바꾸기 준비: 받은 exe를 지금 exe 옆에 복사하고 복사본의 해시를 다시 견준다."""
    reset(folder)
    place = folder / "내 앱"
    place.mkdir(parents=True)
    exe, got = place / "AlgoBlock.exe", folder / "got.exe"
    exe.write_bytes(b"old")
    got.write_bytes(b"new")
    staged = updater.put_beside_exe(exe, got, hashlib.sha256(b"new").hexdigest())
    assert staged == place / ".AlgoBlock.exe.new" and staged.read_bytes() == b"new"
    staged.unlink()
    try:
        updater.put_beside_exe(exe, got, hashlib.sha256(b"other").hexdigest())
        raise AssertionError("해시가 다르면 옆에 두지 않는다")
    except updater.Refused:
        pass
    assert sorted(path.name for path in place.iterdir()) == ["AlgoBlock.exe"]


def handshake_failure(folder: Path) -> None:
    """PowerShell이 기다리기 시작하지 않고 끝나면: 앱은 그대로(거절), 옆에 둔 새 exe는 지우고, 까닭(종료 코드와 출력)은 표준 오류에 남긴다."""
    reset(folder)
    folder.mkdir(parents=True)
    staged = folder / ".AlgoBlock.exe.new"
    staged.write_bytes(b"new")
    (folder / "swap-out.log").write_text("파일을 찾을 수 없다", encoding="utf-8")
    ended = subprocess.Popen([sys.executable, "-c", "raise SystemExit(3)"])
    ended.wait()
    err = io.StringIO()
    with patch.object(updater, "detached", lambda *a, **k: ended), contextlib.redirect_stderr(err):
        try:
            updater.swap_later_exe(folder / "AlgoBlock.exe", staged, pids=[1])
            raise AssertionError("시작하지 않은 스크립트를 믿고 앱을 끝내려 했다")
        except updater.Refused as exc:
            assert "그대로" in str(exc) and "종료 코드" not in str(exc)
    assert not staged.exists() and "종료 코드 3" in err.getvalue() and "파일을 찾을 수 없다" in err.getvalue(), err.getvalue()


def ps_literal(text: str) -> str:
    """PowerShell이 작은따옴표 글을 읽는 대로 되읽는다(시험용): 작은따옴표 꼴 둘이 이어지면 뒤의 것 하나."""
    quotes = "'\u2018\u2019\u201a\u201b"
    assert text[0] in quotes and text[-1] in quotes, text
    out, i, body = [], 0, text[1:-1]
    while i < len(body):
        if body[i] in quotes:
            assert i + 1 < len(body) and body[i + 1] in quotes, f"따옴표가 글을 끊는다: {text}"
            i += 1
        out.append(body[i])
        i += 1
    return "".join(out)


def ps_script(folder: Path) -> None:
    """PowerShell 스크립트의 글: 공백·한글·따옴표·$·` 가 든 경로도 그대로 넘어가고, 본문은 정해진 값만 쓴다."""
    reset(folder / "자료 폴더")
    for name in ("C:\\Program Files\\AlgoBlock\\AlgoBlock.exe", "D:\\내 앱\\김's ‘앱’ $env:X `n\\AlgoBlock.exe", "C:\\a‚b‛c\\AlgoBlock.exe"):
        app = Path(name)
        text = updater.swap_ps1(app, updater.beside(app, "new"), [11, 22], 60, 20, 8800)
        head = dict(line.split(" = ", 1) for line in text.split("\n")[:9])
        assert list(head) == ["$app", "$new", "$old", "$log", "$ready", "$ids", "$wait", "$health", "$url"], head
        assert ps_literal(head["$url"]) == "http://127.0.0.1:8800/"
        assert ps_literal(head["$app"]) == str(app) and ps_literal(head["$new"]) == str(updater.beside(app, "new"))
        assert ps_literal(head["$old"]) == str(updater.beside(app, "old")) and ps_literal(head["$log"]) == str(updater.DIR / "swap.log")
        assert ps_literal(head["$ready"]) == str(updater.DIR / "swap.waiting")
        assert head["$ids"] == "@(11, 22)" and head["$wait"] == "60" and head["$health"] == "20"
    assert updater.swap_ps1(Path("a.exe"), Path("b.exe"), []).split("\n")[5] == "$ids = @()"
    with patch.dict(os.environ, {"ALGOBLOCK_UI_PORT": "9123"}):  # 포트를 주지 않으면 앱과 같은 값을 읽는다
        assert "$url = 'http://127.0.0.1:9123/'" in updater.swap_ps1(Path("a.exe"), Path("b.exe"), [])
    body = updater.SWAP_PS1
    # PowerShell을 이 기기에서 돌리지 못해도 잡을 수 있는 실수: 정하지 않은 변수, 짝이 안 맞는 괄호, 함수를 괄호로 부르기
    used = set(re.findall(r"\$(?:script:)?([A-Za-z_]\w*)", body))
    known = {"app", "new", "old", "log", "ready", "ids", "wait", "health", "url", "true", "false", "null", "_", "env", "PSVersionTable", "PID"}
    assigned = (set(re.findall(r"\$(?:script:)?(\w+) = ", body)) | set(re.findall(r"foreach \(\$(\w+) in", body))
                | set(re.findall(r"\[string\]\$(\w+)", body)) | set(re.findall(r"function [\w-]+\(\$(\w+)\)", body)))
    assert used <= known | assigned, used - known - assigned
    for pair in ("{}", "()", "[]"):
        assert body.count(pair[0]) == body.count(pair[1]), pair
    for name in ("Move-Retry", "Remove-Retry", "Open-App", "Say", "Test-Served", "Stop-Tree", "Undo-Swap"):
        assert not re.search(rf"(?<!function ){name}\(", body), f"PowerShell 함수는 괄호 없이 부른다: {name}"
    assert "exit 1" in body and "finally" in body and "Remove-Retry $ready" in body
    assert undo_only(Path("C:/앱/AlgoBlock.exe")).endswith("\nUndo-Swap\n")  # Windows 시험이 쓰는 '되돌리기만' 글이 본문을 빼고 만들어진다


def env_cleaning(folder: Path) -> None:
    """새 앱이 이 앱의 풀어 놓은 폴더(이 앱이 끝나면 지워진다)를 가리키지 않게 한다: PyInstaller의 표시와,
    값이 그 폴더 아래를 가리키는 변수(런처가 넣는 화면·채점기·모델 폴더)를 걷는다. 런처도 없는 폴더를 가리키는 값은 묶음으로 바꾼다."""
    bundle = os.path.join(tempfile.gettempdir(), "_MEI12345")
    elsewhere = os.path.join(tempfile.gettempdir(), "_MEI12345-not-inside", "data")  # 이름만 비슷한 다른 폴더는 남긴다
    fake = {"_PYI_APPLICATION_HOME_DIR": bundle, "_MEIPASS2": bundle, "PATH": os.pathsep.join([bundle, os.path.join(bundle, "sub"), "/usr/bin"]),
            "KEEP": "1", "ALGOBLOCK_UI_STATIC": os.path.join(bundle, "ui"), "ALGOBLOCK_JUDGE_DIR": os.path.join(bundle, "judge"),
            "ALGOBLOCK_EMBED_DIR": bundle, "ALGOBLOCK_UI_DATA": elsewhere, "RELATIVE": "ui"}
    with patch.dict(os.environ, fake, clear=True), patch.object(sys, "_MEIPASS", bundle, create=True):
        env = updater.clean_env()
    assert env == {"KEEP": "1", "PATH": "/usr/bin", "PYINSTALLER_RESET_ENVIRONMENT": "1", "ALGOBLOCK_UI_DATA": elsewhere, "RELATIVE": "ui"}, env
    # 런처: 물려받은 값이 없는 폴더를 가리키면 이 묶음의 폴더로, 있는 폴더를 가리키면 그대로
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packaging"))
    import launcher

    mine = folder / "묶음"
    kept = folder / "있는 화면"
    kept.mkdir(parents=True)
    gone = {"ALGOBLOCK_UI_STATIC": os.path.join(bundle, "ui"), "ALGOBLOCK_JUDGE_DIR": str(kept), "ALGOBLOCK_UI_DATA": str(folder / "data")}
    with patch.dict(os.environ, gone), patch.object(sys, "_MEIPASS", str(mine), create=True):
        launcher.prepare()
        assert os.environ["ALGOBLOCK_UI_STATIC"] == str(mine / "ui") and os.environ["ALGOBLOCK_EMBED_DIR"] == str(mine / "models")
        assert os.environ["ALGOBLOCK_JUDGE_DIR"] == str(kept)


def pids_to_wait() -> None:
    """onefile이면(풀어 놓는 폴더가 exe 옆이 아니다) 부모 프로세스도 기다린다. onedir(_internal)이면 이 프로세스만."""
    exe = os.path.join(tempfile.gettempdir(), "앱", "AlgoBlock.exe")
    for bundle, both in ((os.path.join(tempfile.gettempdir(), "_MEI777"), True), (os.path.join(os.path.dirname(exe), "_internal"), False),
                         (os.path.dirname(exe), False)):
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", exe), patch.object(sys, "_MEIPASS", bundle, create=True):
            assert updater.app_pids() == ([os.getpid(), os.getppid()] if both else [os.getpid()]), bundle


def settings_safety(folder: Path) -> None:
    """설정 파일이 있는데 읽지 못하면 기본값으로 덮어쓰지 않는다(자동 확인 끔·건너뛴 버전을 잃지 않게). 깨진 파일은 새로 쓴다."""
    reset(folder)
    updater.save(auto=False, skip="0.1.1")
    file = folder / "settings.json"
    file.chmod(0)
    try:
        if not os.access(file, os.R_OK):  # 관리자 권한이나 Windows면 권한 비트가 막지 못한다
            try:
                updater.save(checked=1.0)
                raise AssertionError("읽지 못한 설정 위에 덮어썼다")
            except OSError:
                pass
    finally:
        file.chmod(0o600)
    assert updater.settings()["auto"] is False and updater.settings()["skip"] == "0.1.1"
    file.write_text("{깨짐", encoding="utf-8")
    updater.save(auto=False)
    assert updater.settings()["auto"] is False


def clock_back(folder: Path) -> None:
    """도는 중에 시계가 크게 뒤로 가면, 멀어진 다음 확인을 기다리지 않고 바로 묻는다."""
    reset(folder)
    calls = []
    with patch.object(updater, "check", lambda: calls.append(True) or True):
        updater.PLAN.update(due=1_000_000.0 + 3 * 24 * 3600, fails=0)
        updater.tick(1_000_000.0)
    assert calls and updater.PLAN["due"] == 1_000_000.0 + 24 * 3600


def swap_notes(folder: Path) -> None:
    """지난번 바꾸기의 기록을 한 번만 읽는다. 되돌렸거나 바꾸지 못했으면 화면에 알릴 글을 만든다."""
    reset(folder)
    folder.mkdir(parents=True)
    assert updater.last_swap_note() == ""  # 기록이 없다
    (folder / "swap.log").write_text("시작: A\n새 앱이 응답하지 않아 되돌린다\n되돌렸다\n열었다: A\n", encoding="utf-8")
    note = updater.last_swap_note()
    assert "마치지 못해" in note and str(folder / "swap.prev.log") in note and not (folder / "swap.log").exists()
    assert updater.last_swap_note() == ""  # 한 번만
    (folder / "swap.log").write_text("시작: A\n열었다: A\n바꿨다\n", encoding="utf-8")
    assert updater.last_swap_note() == ""
    # 바꾸는 스크립트가 아직 도는 중이면(새 앱이 켜진 때) 기록을 건드리지 않는다
    (folder / "swap.log").write_text("시작: A\n열었다: A\n", encoding="utf-8")
    (folder / "swap.waiting").write_text("waiting", encoding="utf-8")
    assert updater.last_swap_note() == "" and (folder / "swap.log").exists()
    (folder / "swap.waiting").unlink()


def windows_swapping(folder: Path) -> None:
    """Windows에서만: 임시 폴더의 가짜 exe 둘로 PowerShell 스크립트를 돌려 본다 — 바꾸기(로컬 서버가 응답함), 새 앱이 열리지 않거나
    응답하지 않을 때 되돌리기, 앱이 끝나지 않을 때·앱을 잡지 못할 때 아무것도 바꾸지 않기, 그리고 앱에서 떼어 띄우기.
    새 앱은 진짜 AlgoBlock이 아니라서, '새 앱의 서버'는 이 시험이 띄운 작은 HTTP 서버가 대신한다(스크립트의 판단만 본다)."""
    if os.name != "nt":
        return
    import http.server
    import socket

    reset(folder)
    folder.mkdir(parents=True)
    real = Path(os.environ.get("SystemRoot") or r"C:\Windows") / "System32" / "hostname.exe"  # 인자 없이 열면 바로 0으로 끝난다
    base = real.read_bytes()
    log = folder / "swap.log"

    class Ok(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    served = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Ok)
    threading.Thread(target=served.serve_forever, daemon=True).start()
    with socket.socket() as probe:  # 아무도 듣지 않는 포트(새 앱이 응답하지 않는 경우)
        probe.bind(("127.0.0.1", 0))
        silent = probe.getsockname()[1]

    def exe(path: Path, mark: bytes) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base + mark)  # 끝에 붙인 바이트는 실행에 상관없고, 어느 쪽인지 알아보는 표시다
        return path

    def alive(seconds: float) -> subprocess.Popen:
        return subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({seconds})"])

    def run(app: Path, new: Path, pids: list[int], wait: int = 15, port: int = served.server_address[1]) -> tuple[int, str]:
        script = folder / "swap.ps1"
        script.write_text(updater.swap_ps1(app, new, pids, wait, 5, port), encoding="utf-8-sig")
        out = subprocess.run([str(updater.POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                             capture_output=True, timeout=180)
        text = log.read_text(encoding="utf-8") if log.exists() else ""
        log.unlink(missing_ok=True)
        assert not (folder / "swap.waiting").exists(), "끝나면 '기다리는 중' 표시를 지운다"
        return out.returncode, text + out.stdout.decode("utf-8", "replace") + out.stderr.decode("utf-8", "replace")

    def names(place: Path) -> list[str]:
        return sorted(path.name for path in place.iterdir())

    launch_probe(folder / "probe")
    try:
        windows_cases(folder, exe, alive, run, names, log, silent)
    finally:
        served.shutdown()
        served.server_close()


def launch_probe(folder: Path) -> None:
    """진단(단정하지 않는다): 떼어 띄우는 방법마다 작은 PowerShell 스크립트가 시작해 표시를 쓰는지 찍는다. 띄우기가 실패할 때 원인을 가린다."""
    folder.mkdir(parents=True)
    for name, flags in (("CREATE_NO_WINDOW", updater.CREATE_NO_WINDOW | updater.CREATE_NEW_PROCESS_GROUP),
                        ("DETACHED_PROCESS", updater.DETACHED_PROCESS | updater.CREATE_NEW_PROCESS_GROUP)):
        mark, out = folder / f"{name}.mark", folder / f"{name}.out"
        script = folder / f"{name}.ps1"
        script.write_text(f"[IO.File]::WriteAllText({updater.ps_text(mark)}, 'ok')\nexit 7\n", encoding="utf-8-sig")
        try:
            process = updater.detached([str(updater.POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)], out, flags)
            code = process.wait(60)
        except Exception as exc:  # noqa: BLE001 - 진단이다
            code = f"{type(exc).__name__}: {exc}"
        print(f"launch probe {name}: 종료 코드 {code}(7이면 끝까지 돌았다), 표시 {'있음' if mark.exists() else '없음'}, 출력 {updater.tail(out, 600)!r}", flush=True)


def undo_only(app: Path) -> str:
    """스크립트의 함수들만 두고 Undo-Swap 하나를 부르는 글(시험용). 첫 줄에서 시작하는 'try {'가 본문의 시작이다."""
    functions = updater.swap_ps1(app, updater.beside(app, "new"), [], 5, 5).split("\ntry {\n", 1)[0]
    assert "function Undo-Swap" in functions and "스크립트 시작" not in functions
    return functions + "\nUndo-Swap\n"


def windows_cases(folder, exe, alive, run, names, log, silent) -> None:
    # 0. 되돌리기만(Undo-Swap): 새 exe가 이미 없으면(백신이 격리 등) 치우기를 건너뛰고 옛 exe를 제자리로. 있으면 치우고 제자리로
    for has_new in (False, True):
        app = folder / f"되돌리기만 {has_new}" / "AlgoBlock.exe"
        exe(updater.beside(app, "old"), b"old")
        if has_new:
            exe(app, b"new")
        script = folder / "undo.ps1"
        script.write_text(undo_only(app), encoding="utf-8-sig")
        out = subprocess.run([str(updater.POWERSHELL), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                             capture_output=True, timeout=180)
        text = (log.read_text(encoding="utf-8") if log.exists() else "") + out.stderr.decode("utf-8", "replace")
        log.unlink(missing_ok=True)
        assert "되돌렸다" in text, text
        assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 1. 바꾸기: 앱이 끝나기를 기다렸다가 새 exe를 넣고 열고, 서버가 응답하면 옛 exe를 지운다
    #    (앱 프로세스는 스크립트가 잡을 때까지 살아 있어야 한다. PowerShell이 뜨는 데 1~2초 걸린다)
    app = exe(folder / "바꾸기 'ok' 폴더" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    process = alive(4)
    began = time.monotonic()
    code, text = run(app, new, [process.pid])
    assert code == 0 and "바꿨다" in text and "열었다" in text, text
    assert time.monotonic() - began >= 3.5, "앱이 끝나기 전에 바꾸면 안 된다"
    assert app.read_bytes().endswith(b"new") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 2. 새 exe가 열리지 않으면(실행 파일이 아니다) 옛 exe를 되돌리고 연다
    app = exe(folder / "되돌리기" / "AlgoBlock.exe", b"old")
    updater.beside(app, "new").write_bytes(b"not an exe")
    code, text = run(app, updater.beside(app, "new"), [alive(4).pid])
    assert code == 1 and "되돌렸다" in text and "열었다" in text, text
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 2-1. 새 exe는 열렸지만 서버가 응답하지 않으면(오류로 끝남, 떠 있지만 깨짐) 옛 exe를 되돌리고 연다
    app = exe(folder / "응답 없음" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    code, text = run(app, new, [alive(4).pid], port=silent)
    assert code == 1 and "응답하지 않아" in text and "되돌렸다" in text, text
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 2-2. 앱 프로세스를 잡지 못하면(이미 없다) 기다릴 수 없으니 바꾸지 않고, '기다리는 중' 표시도 남기지 않는다
    app = exe(folder / "못 잡음" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    gone = alive(0)
    gone.wait()
    code, text = run(app, new, [gone.pid])
    assert code == 1 and "잡지 못해" in text and "열었다" not in text, text
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 3. 앱이 끝나지 않으면 아무것도 바꾸지 않고 열지도 않는다(앱은 아직 떠 있다)
    app = exe(folder / "안 끝남" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    stuck = alive(60)
    try:
        code, text = run(app, new, [stuck.pid], wait=2)
    finally:
        stuck.kill()
    assert code == 1 and "앱이 끝나지 않아" in text and "열었다" not in text, text
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 3-1. 앱은 끝났는데 부모 프로세스(onefile)가 끝나지 않으면 바꾸지 않고 옛 앱을 다시 연다
    app = exe(folder / "부모 안 끝남" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    ended, stuck = alive(4), alive(60)  # 앱은 스크립트가 잡은 뒤에 끝나고, 부모는 끝나지 않는다
    try:
        code, text = run(app, new, [ended.pid, stuck.pid], wait=8)
    finally:
        stuck.kill()
    assert code == 1 and "부모 프로세스가 끝나지 않아" in text and "열었다" in text, text
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)

    # 4. 앱에서 떼어 띄우기: 스크립트가 이 프로세스를 잡고 기다리기 시작한 것을 보고 돌아온다(이 시험 프로세스는 끝나지 않으니 바꾸지 않는다)
    app = exe(folder / "떼어 띄우기" / "AlgoBlock.exe", b"old")
    new = exe(updater.beside(app, "new"), b"new")
    script = updater.swap_later_exe(app, new, pids=[os.getpid()], wait=2, health=5)
    script.wait(60)  # 스크립트가 끝나 로그를 놓은 뒤에 보고 지운다(임시 폴더 정리가 쥔 파일에 막히지 않게)
    text = log.read_text(encoding="utf-8") if log.exists() else (folder / "swap-out.log").read_text(encoding="utf-8", errors="replace")
    assert script.returncode == 1 and "끝나지 않아" in text, text
    assert not (folder / "swap.waiting").exists() and not new.exists()
    assert app.read_bytes().endswith(b"old") and names(app.parent) == ["AlgoBlock.exe"], names(app.parent)


@patch.object(updater, "VERSION", "0.1.0")  # 시험은 지금 앱을 0.1.0으로, 새 릴리스를 0.1.1로 둔다(실제 버전을 올려도 맞게). 끝나면 원래 값으로 돌아간다
def run() -> None:
    with tempfile.TemporaryDirectory(prefix="algoblock-update-test-") as tmp:
        root = Path(tmp)
        before = updater.DIR
        versions()
        picking()
        hashes()
        checking(root / "check")
        dev_build(root / "dev")
        downloading(root / "download")
        installing(root / "install")
        if os.name != "nt":  # 바꿔 끼우기(swap.sh)는 macOS의 .app에만 있는 기능이고 /bin/sh로 돈다. Windows에는 /bin/sh가 없고 이 길을 타지 않는다
            swapping(root / "swap")
        tidying(root / "tidy")
        scheduling(root / "schedule")
        remembering(root / "remember")
        stalling(root / "stall")
        staging(root / "stage")
        handshake_failure(root / "handshake")
        ps_script(root / "ps")
        env_cleaning(root / "env")
        pids_to_wait()
        settings_safety(root / "settings")
        clock_back(root / "clock")
        swap_notes(root / "notes")
        windows_swapping(root / "windows")
        reset(before)
        updater.PLAN.update(due=0.0, fails=0)


def exe_swapping(built: Path) -> None:
    """Windows CI에서: 빌드한 진짜 exe의 사본 둘(수정 시각만 다르다)로 바꿔 끼우기를 끝까지 본다. 시간은 swap.log와 작업 요약에 남긴다.
    1. 성공: 옛 앱(--server)이 떠 있는 동안 스크립트를 떼어 띄우고, 옛 앱을 끝내면 새 exe로 바꿔 열고 새 앱의 `/`가 200을 준다.
    2. 되돌리기: 새 앱의 포트를 다른 소켓이 막아 응답하지 않으면, 새 앱을 끝내고 옛 exe를 되돌려 연다."""
    import shutil
    import socket
    import urllib.request

    old_time, new_time = 946684800, 978307200  # 2000-01-01, 2001-01-01: 어느 사본이 제자리에 있는지 알아보는 표시(이름 바꾸기는 수정 시각을 그대로 둔다)
    root = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()) / "업데이트 시험 'exe'"
    shutil.rmtree(root, ignore_errors=True)
    summary = []

    def served(port: int) -> bool:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3) as response:
                return response.status == 200
        except OSError:
            return False

    def prepare(name: str, port: int) -> Path:
        """옛 exe를 둔다. 앱과 시험이 같은 자료 폴더를 쓴다(실제처럼: 켤 때의 정리가 '바꾸는 중' 표시를 보고 옛 exe를 남긴다)."""
        os.environ["ALGOBLOCK_UI_PORT"] = str(port)
        os.environ["ALGOBLOCK_UI_DATA"] = str(root / name / "data")
        updater.DIR = root / name / "data" / "updates"  # server.py와 같은 자리
        app = root / name / "app" / "AlgoBlock.exe"
        app.parent.mkdir(parents=True)
        shutil.copyfile(built, app)
        os.utime(app, (old_time, old_time))
        return app

    def stage(app: Path) -> Path:
        """새 exe를 옆에 둔다. 실제처럼 옛 앱이 켜진 뒤에(켤 때의 정리는 남은 .new를 지운다)."""
        new = updater.beside(app, "new")
        shutil.copyfile(built, new)
        os.utime(new, (new_time, new_time))
        return new

    def finish(script: subprocess.Popen, name: str, app: Path) -> str:
        script.wait(600)
        log = (updater.DIR / "swap.log").read_text(encoding="utf-8")
        files = [f"{path.name}({path.stat().st_size}바이트, 수정 {int(path.stat().st_mtime)})" for path in sorted(app.parent.iterdir()) if path.is_file()]
        print(f"--- {name}: 스크립트 종료 코드 {script.returncode}\n{log}[폴더] {', '.join(files)}\n[swap-out.log] {updater.tail(updater.DIR / 'swap-out.log', 800)}", flush=True)
        summary.extend(f"{name}: {line.split(' ', 2)[-1]}" for line in log.splitlines() if "응답" in line or "되돌" in line or "바꿨다" in line)
        return log

    def kill_apps() -> None:
        subprocess.run(["taskkill", "/IM", "AlgoBlock.exe", "/T", "/F"], capture_output=True)

    try:
        # 1. 성공
        app = prepare("성공", 8803)
        old = subprocess.Popen([str(app), "--server"])
        began = time.monotonic()
        while not served(8803):
            assert old.poll() is None and time.monotonic() - began < 300, "옛 앱(--server)이 뜨지 않았다"
            time.sleep(1)
        summary.append(f"성공: 옛 앱(--server)이 응답하기까지 {time.monotonic() - began:.1f}초")
        new = stage(app)
        script = updater.swap_later_exe(app, new, pids=[old.pid], port=8803)
        subprocess.run(["taskkill", "/PID", str(old.pid), "/T", "/F"], capture_output=True)  # 앱이 끝난다(업데이트의 quit_app 자리)
        log = finish(script, "성공", app)
        assert script.returncode == 0 and "바꿨다" in log and "응답했다" in log, log
        assert app.stat().st_mtime == new_time and not new.exists() and not updater.beside(app, "old").exists()
        assert served(8803), "바꾼 뒤 새 앱의 / 가 200을 주지 않는다"
        summary.append("성공: 바꾼 뒤 새 앱의 / 가 200")
        kill_apps()

        # 2. 되돌리기
        app = prepare("되돌리기", 8804)
        new = stage(app)
        blocker = socket.socket()
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)  # 새 앱이 같은 포트에 겹쳐 묶지 못하게
        blocker.bind(("127.0.0.1", 8804))
        blocker.listen(1)  # 받기만 하고 답하지 않는다
        try:
            sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(8)"])
            script = updater.swap_later_exe(app, new, pids=[sleeper.pid], health=30, port=8804)
            log = finish(script, "되돌리기", app)
        finally:
            blocker.close()
            kill_apps()
        assert script.returncode == 1 and "응답하지 않아" in log and "되돌렸다" in log, log
        assert app.stat().st_mtime == old_time and not new.exists() and not updater.beside(app, "old").exists()
    finally:
        kill_apps()
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
                out.write("### exe 바꿔 끼우기(Windows)\n" + "".join(f"- {line}\n" for line in summary))
        print("\n".join(summary))


if __name__ == "__main__":
    if sys.argv[1:2] == ["exe"]:  # Windows CI: python -B ui/test_update.py exe <빌드한 exe>
        exe_swapping(Path(sys.argv[2]).resolve())
    else:
        run()
    print("ok")
