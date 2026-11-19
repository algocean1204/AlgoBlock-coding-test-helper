"""화면 흐름 시험: 서버를 가짜 모델로 띄우고 flow/*.mjs를 브라우저로 돌린다. 모델·네트워크를 쓰지 않는다.

준비: cd app/ui/stageshow && npm ci --ignore-scripts    (playwright-core. 브라우저는 깔린 Chrome, CHROME_PATH로 바꾼다)
실행: cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B ui/test_flow.py [사진 폴더]
흐름 스크립트는 `node <스크립트> <서버 주소> <사진 폴더>`로 불린다. 서버 밖 요청은 막고 실패로 적으며,
실패하면 사진 폴더에 화면 사진을 남기고 1로 끝난다. 모두 통과하면 끝에 ok를 찍는다.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="algoblock-flow-"))
(TMP / "data").mkdir()
os.environ["ALGOBLOCK_UI_DATA"] = str(TMP / "data")  # 사용자 데이터 폴더를 건드리지 않는다
os.environ["ALGOBLOCK_UI_PREPARE"] = "0"
for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_MODEL", "ALGOBLOCK_LLM_PROVIDER", "ALGOBLOCK_UI_CLIENT", "ALGOBLOCK_EVAL_EXTRA", "ALGOBLOCK_UI_SCENARIOS"):
    os.environ.pop(name, None)  # 키 없이 돈다
sys.path.insert(0, str(HERE))

import server  # noqa: E402
from tutor.llm import FakeLlm, use_llm  # noqa: E402

server.ROOT = TMP  # 저장소의 .env를 읽지 않는다
FAKE = FakeLlm()  # 응답이 없어 부르면 실패한다. 부른 기록은 FAKE.calls에 남는다
server.model = lambda: use_llm(FAKE)  # 요청을 받는 스레드마다 가짜 모델을 건다(문맥 변수는 새 스레드로 넘어가지 않는다)
ASKED: list[str] = []  # 업데이트 확인이 부르려 한 주소(네트워크로 나가지 않고 실패로 센다)


def no_network(url, *args, **kwargs):
    ASKED.append(str(url))
    raise OSError("흐름 시험은 네트워크를 쓰지 않는다")


server.updater.fetch = no_network
VIEWPORTS = ("1366x689", "1093x551")


def serve(handler) -> tuple[ThreadingHTTPServer, str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)  # 빈 포트
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_port}"


def run(script: Path, base: str, shots: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(script), base, str(shots)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def scripted(script: Path):
    """같은 이름의 .json이 있으면 그 흐름 동안만 가짜 모델에 응답 대본({"scripts": {task: [응답…]}})을 걸고 환경 변수({"env": {…}})를 둔다.
    대본이 답한 호출은 허용하고(그 흐름 동안 쌓인 기록에서 그만큼 지운다), 대본 밖의 호출과 대본이 없는 흐름의 호출은 남아 실패가 된다.
    쓰지 않고 남은 대본은 main이 실패로 센다. 환경은 끝나면 되돌린다."""
    plan = script.with_suffix(".json")
    if not plan.exists():
        yield
        return
    data = json.loads(plan.read_text(encoding="utf-8"))
    saved = {name: os.environ.get(name) for name in data.get("env", {})}
    os.environ.update(data.get("env", {}))
    FAKE.scripts = {task: list(items) for task, items in data.get("scripts", {}).items()}
    budget, start = {task: len(items) for task, items in FAKE.scripts.items()}, len(FAKE.calls)
    try:
        yield
    finally:
        mine = FAKE.calls[start:]
        del FAKE.calls[start:]
        for call in mine:
            if budget.get(call["task"], 0) > 0:
                budget[call["task"]] -= 1
            else:
                FAKE.calls.append(call)
        FAKE.scripts = {}
        for name, value in saved.items():
            os.environ.pop(name, None) if value is None else os.environ.__setitem__(name, value)


PROBE = "http://203.0.113.7/probe.png"  # 문서용 주소(어디로도 가지 않는다)


def self_check(script: Path, base: str) -> None:
    """흐름을 일부러 실패시켜 본다: 앱이 아닌 빈 화면(base)이 서버 밖 주소를 부르면 막아서 적고, 뷰포트마다 사진을 남기고 1로 끝나야 한다."""
    shots = TMP / f"broken-{script.stem}"
    out = run(script, base, shots)
    names = " ".join(path.name for path in shots.glob("*.png"))
    if out.returncode != 1 or f"external: {PROBE}" not in out.stderr or not all(tag in names for tag in VIEWPORTS):
        raise AssertionError(f"{script.name}: 실패를 잡지 못했다(종료 {out.returncode}, 사진 [{names}])\n{out.stdout}{out.stderr}")


def short_waits(script: Path) -> list[str]:
    """기본 대기를 줄인 흐름(setDefaultTimeout)의 서버 요청(request.post·get)과 페이지 이동(goto·reload)은 timeout을 따로 준다:
    준비 요청과 페이지를 여는 일이 느린 러너에서 화면 대기 기본값에 끊기지 않게."""
    text = script.read_text(encoding="utf-8")
    if "setDefaultTimeout(" not in text:
        return []
    return [f"{script.name}:{n}" for n, line in enumerate(text.splitlines(), 1) if re.search(r"request\.(post|get)\(|\.(goto|reload)\(", line) and "timeout:" not in line]


def main() -> bool:
    keep = len(sys.argv) > 1  # 사진 폴더를 받았으면 그대로 둔다. 없으면 실패할 때만 남는 새 폴더에 찍는다
    shots = Path(sys.argv[1]).resolve() if keep else Path(tempfile.mkdtemp(prefix="algoblock-flow-shots-"))
    scripts = sorted((HERE / "flow").glob("*.mjs"))
    failed = []
    try:
        assert scripts, "flow/*.mjs가 없다"
        loose = [where for script in scripts for where in short_waits(script)]
        assert not loose, f"기본 대기를 줄인 흐름의 서버 요청·페이지 이동에 timeout이 없다(같은 줄에 적는다): {loose}"
        page = TMP / "broken"
        page.mkdir()
        (page / "index.html").write_text(f'<!doctype html><meta charset="utf-8"><title>빈 화면</title><img src="{PROBE}" alt="">', encoding="utf-8")
        blank, empty = serve(partial(Quiet, directory=str(page)))
        try:  # 빈 화면에서는 스크립트마다 시간 초과를 기다려 오래 걸린다. 함께 돌린다
            with ThreadPoolExecutor(4) as pool:
                list(pool.map(lambda script: self_check(script, empty), scripts))
        finally:
            blank.shutdown()
        httpd, base = serve(server.Handler)
        try:
            for script in scripts:
                # 처음 안내 창이 화면을 가리지 않게. 흐름마다 이 값으로 되돌려 앞 흐름이 실패하며 남긴 설정(마지막 언어 등)을 넘기지 않는다
                (TMP / "data" / "prefs.json").write_text(json.dumps({"tour_seen": True}), encoding="utf-8")
                with scripted(script):
                    out = run(script, base, shots)
                    left = {task: len(items) for task, items in FAKE.scripts.items() if items}
                print(f"== {script.name}\n{out.stdout}{out.stderr}", end="", flush=True)
                if out.returncode:
                    failed.append(script.name)
                if left:
                    failed.append(f"{script.name}: 쓰지 않은 대본 {left}")
        finally:
            httpd.shutdown()
            httpd.server_close()
        if FAKE.calls:
            failed.append(f"모델 {len(FAKE.calls)}회: {[call['task'] for call in FAKE.calls]}")
        if ASKED:
            failed.append(f"네트워크 {len(ASKED)}회: {ASKED}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)  # 실패하거나 예외가 나도 임시 자료 폴더는 지운다
    if failed:
        print(f"실패: {failed}. 화면 사진: {shots}", file=sys.stderr)
        return False
    if not keep:
        shutil.rmtree(shots, ignore_errors=True)
    print("ok")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
