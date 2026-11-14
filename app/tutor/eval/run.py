"""평가 세트를 실모델로 돌려 결과를 남긴다. 지금은 A4 블록 설계만 돈다.

app에서:       python3 -m tutor.eval.run
결과: eval/results/<날짜>.jsonl 에 한 문제 한 줄로 덧붙인다.
"""

import json
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from ..common.errors import llm_error
from ..llm import LlmError, model_name
from ..plan.graph import graph as plan_graph
from ..state import TutorContext, TutorRequest

HERE = Path(__file__).resolve().parent


def is_correct(stem: str, plan) -> bool:
    """파일 이름이 정답 유형이다. out_of_scope.md는 범위 밖 표시가 서야 맞다."""
    if plan is None:
        return False
    if stem == "out_of_scope":
        return plan.out_of_scope
    return plan.algorithm == stem and not plan.out_of_scope


def run_one(path: Path) -> dict:
    ctx = TutorContext(problem_id=path.stem, problem_text=path.read_text(encoding="utf-8"), language="python")
    state = {"request": TutorRequest(kind="explain", problem_id=path.stem), "ctx": ctx, "open_count": 0}
    row = {"problem": path.stem, "agent": "plan", "model": model_name(), "correct": False}
    began = time.monotonic()
    try:
        done = plan_graph().invoke(state)
        error = done.get("error")
        row["error"] = asdict(error) if error else None
        row["plan"] = asdict(done["plan"]) if done.get("plan") else None
        row["correct"] = is_correct(path.stem, done.get("plan"))
    except LlmError as exc:
        row["error"] = asdict(llm_error(exc))
    row["seconds"] = round(time.monotonic() - began, 1)
    return row


def main() -> int:
    problems = sorted((HERE / "problems").glob("*.md"))
    if not problems:
        print("eval/problems/ 에 문제 글을 넣으세요. 이름은 README.md 표를 따릅니다.")
        return 1
    out = HERE / "results" / f"{date.today()}.jsonl"
    out.parent.mkdir(exist_ok=True)
    right = 0
    with out.open("a", encoding="utf-8") as file:
        for path in problems:
            row = run_one(path)
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            if row["error"]:
                status = row["error"]["code"]
            else:
                plan = row["plan"]
                status = f"{plan['algorithm']}{' 범위 밖' if plan['out_of_scope'] else ''}, 블록 {len(plan['blocks'])}개"
            print(f"{'O' if row['correct'] else 'X'} {path.stem}: {status} ({row['seconds']}초)")
            right += row["correct"]
    print(f"유형 정답 {right}/{len(problems)}")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
