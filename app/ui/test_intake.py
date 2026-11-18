"""내 문제 넣기 한 화면: (1) 정적 계약 — 걸음 표시와 3걸음 요약이 없고, 감지 줄과 두 칸 자리가 있다(index.html·app.js만 본다).
(2) 키가 없을 때 — 준비를 켠 서버(ALGOBLOCK_UI_PREPARE 기본값)에서도 등록한 문제가 '준비 중'이나 '숨은 테스트 만드는 중'에 걸리지 않고 예시만으로 채점된다.
실행: cd app && python3.14 -B ui/test_intake.py   (끝에 ok. 화면 흐름은 flow/intake.mjs가 본다)
"""

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = (HERE / "index.html").read_text(encoding="utf-8")
APP = (HERE / "app.js").read_text(encoding="utf-8")
CSS = (HERE / "app.css").read_text(encoding="utf-8")


def ids(source: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', source))


def keyless() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="algoblock-intake-"))
    os.environ["ALGOBLOCK_UI_DATA"] = str(tmp / "data")
    os.environ.pop("ALGOBLOCK_UI_PREPARE", None)  # 준비를 켠 서버(기본값)
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_MODEL", "ALGOBLOCK_LLM_PROVIDER", "ALGOBLOCK_UI_CLIENT", "ALGOBLOCK_EVAL_EXTRA", "ALGOBLOCK_UI_SCENARIOS"):
        os.environ.pop(name, None)
    sys.path.insert(0, str(HERE))
    import server

    try:
        server.ROOT = tmp  # 저장소의 .env를 읽지 않는다
        assert server.PREPARE is True and not server.connected(), "준비는 켜져 있고 모델은 연결되지 않은 상태여야 한다"
        body = {"title": "두 수 더하기", "text": "두 수 a, b의 합을 return 하도록 solution 함수를 완성하세요.", "cases": [{"input": "[1, 2]", "expected": "3"}, {"input": "[5, 5]", "expected": "10"}]}
        pid = server.register(body)["id"]
        state = server.handle("/api/state", {"id": pid, "open": True})[1]["problem"]
        assert state["preparing"] is False and state["checking"] is False and not state.get("hold"), state
        assert pid not in server.PREPARING and pid not in server.PREPARED and pid not in server.CHECKING, "키가 없는데 준비가 시작됐다"
        held = server.register({**body, "text": body["text"] + " ", "problem": False})["id"]
        assert server.handle("/api/state", {"id": held, "open": True})[1]["problem"]["hold"] is True and held not in server.PREPARED  # 문제 아님: 열어도 준비하지 않는다
        done = server.handle("/api/run", {"id": pid, "code": "def solution(a, b):\n    return a + b\n"})[1]
        assert done["status"] == "passed", done  # 예시 채점은 된다
    finally:
        shutil.rmtree(tmp, ignore_errors=True)  # 실패해도 임시 자료 폴더는 지운다


def main() -> None:
    form = INDEX[INDEX.index('id="view-new"'):INDEX.index('id="view-code"')]
    gone = ("wsteps", "wstep-title", "new-next", "new-back", "new-summary", "data-wstep", 'data-step="')
    left = [name for name in gone if name in form]
    assert not left, f"넣기 화면에 걸음 표시·요약이 남아 있다: {left}"
    new = {"detect-line", "intake-problem", "intake-io", "preview", "raw-edit", "case-edit", "noise-show", "noise-lines", "detect-suggest"}
    missing = sorted(new - ids(form))
    assert not missing, f"넣기 화면에 없는 자리: {missing}"
    keep = {"new-text", "new-title", "case-rows", "new-more", "new-submit", "new-mode", "new-many", "new-float", "new-error", "new-clear", "new-form", "edit-confirm", "edit-yes", "edit-no", "case-add"}
    lost = sorted(keep - ids(form))
    assert not lost, f"기존 칸 id가 사라졌다: {lost}"
    for name in ("WSTEP", "WSTEP_TITLE", "setStep", "nextStep", "renderSummary"):
        assert not re.search(rf"\b{name}\b", APP), f"app.js에 걸음 코드가 남아 있다: {name}"
    assert ".wstep-title" not in CSS, "app.css에 걸음 제목 스타일이 남아 있다"
    assert "/api/problems/detect" in APP, "app.js가 감지 API를 부르지 않는다"
    assert re.search(r"touched", APP), "app.js가 고친 칸(touched)을 보내지 않는다"
    assert re.search(r"DOMParser", APP) and "text/html" in APP, "HTML 붙여 넣기를 읽지 않는다"
    keyless()
    print("ok")


if __name__ == "__main__":
    main()
    sys.exit(0)
