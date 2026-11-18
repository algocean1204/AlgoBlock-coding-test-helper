"""내 문제 넣기 한 화면의 정적 계약: 걸음 표시와 3걸음 요약이 없고, 감지 줄과 두 칸 자리가 있다. 서버·브라우저 없이 index.html·app.js만 본다.
실행: python3 -B ui/test_intake.py   (끝에 ok. 화면 흐름은 flow/intake.mjs가 본다)
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = (HERE / "index.html").read_text(encoding="utf-8")
APP = (HERE / "app.js").read_text(encoding="utf-8")
CSS = (HERE / "app.css").read_text(encoding="utf-8")


def ids(source: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', source))


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
    print("ok")


if __name__ == "__main__":
    main()
    sys.exit(0)
