"""업데이트 확인(updater.py). 네트워크는 가짜로 바꾼다. 바꿔 끼우기는 임시 폴더의 가짜 .app 둘로 셸 스크립트를 돌려 본다.

실행: cd app && python3 -B ui/test_update.py     (test_server.py도 이것을 부른다)
"""

import contextlib
import hashlib
import io
import json
import os
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
        if os.access(locked, os.W_OK):  # 관리자 권한으로 돌면 권한 비트가 막지 못한다
            return
        with patch.object(updater, "current_app", lambda: app):
            assert updater.view()["can_install"] is False
            try:
                updater.install(lambda: None)
                raise AssertionError("쓸 수 없는 곳의 앱은 바꾸지 않는다")
            except updater.Refused as exc:
                assert "직접 바꿔 주세요" in str(exc) and str(folder / DMG) in str(exc)
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


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="algoblock-update-test-") as tmp:
        root = Path(tmp)
        before = updater.DIR
        versions()
        picking()
        hashes()
        checking(root / "check")
        downloading(root / "download")
        installing(root / "install")
        swapping(root / "swap")
        tidying(root / "tidy")
        reset(before)


if __name__ == "__main__":
    run()
    print("ok")
