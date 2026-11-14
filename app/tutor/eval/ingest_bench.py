"""문제 넣기 측정: 모델·추론 정도마다 풀이 가이드가 채점을 통과하는가, 몇 번 만에 통과하는가, 블록과 질문이 한 번에 나오는가, 얼마나 걸리는가.

app에서(모델을 부른다):
  python3 -m tutor.eval.ingest_bench 문제파일.json --model claude/claude-sonnet-5-5:high --runs 2
  python3 -m tutor.eval.ingest_bench ui/builtin.json --per-theme 1 --model claude/claude-opus-5-5:high

문제 파일은 [{id, theme, title, text, cases}] 꼴이다(ui/builtin.json이 이 꼴이다). 문제마다 새 저장소에서 미리 만들기(Tutor.prepare)를 그대로 돌린다.
잰 것은 정해진 답이 있는 것뿐이다(채점 통과, 호출 수, 시간, 토큰). 질문의 말씨 같은 품질은 재지 않는다.
결과는 tutor/eval/results/ingest-<시각>-<모델>.json에 남는다(이 폴더는 git에 올리지 않는다).
"""

import argparse
import json
import os
import statistics
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar, copy_context
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ..llm.client import _backend_session
from ..main import Tutor
from .drive import debug_report

NOW: ContextVar[str] = ContextVar("ingest_bench_problem", default="")
CALLS: dict[str, list] = defaultdict(list)  # 실행 이름 → 모델 호출 기록


def one(problem: dict, run: int) -> dict:
    name = f"{problem['id']}#{run}"
    NOW.set(name)
    scenario = SimpleNamespace(language="python", cases=problem["cases"], text=problem["text"])
    checks = []

    def check(_pid, code):
        report = debug_report(scenario, code)
        checks.append(report["status"])
        return report

    began = time.perf_counter()
    with tempfile.TemporaryDirectory() as folder:
        tutor = Tutor(str(Path(folder) / "tutor.db"), check=check)
        try:
            tutor.store.put_problem(problem["id"], "python", problem["text"], title=problem["title"])
            done = tutor.prepare(problem["id"])
            ctx = tutor.store.load(problem["id"])
        finally:
            tutor.close()
    calls = CALLS[name]
    guide, plan = ctx.solution, ctx.plan
    return {
        "id": problem["id"], "run": run, "status": done.status, "seconds": round(time.perf_counter() - began, 1),
        "planned": plan is not None, "verified": bool(guide and guide.verified), "first_try": bool(guide and guide.verified) and len(checks) == 1,
        "solve_calls": sum(c["task"] == "plan.solve" for c in calls), "draft_calls": sum(c["task"] == "plan.draft_blocks" for c in calls),
        "hint_calls": sum(c["task"] == "plan.hints" for c in calls), "checks": checks,
        "blocks": len(plan.blocks) if plan else 0, "empty_hint_blocks": sum(not b.hints for b in plan.blocks) if plan else 0,
        "tiled": bool(plan and guide) and "\n".join(b.reference for b in plan.blocks) == guide.code,
        "input_tokens": sum(c["input"] + c["cache_read"] + c["cache_write"] for c in calls), "output_tokens": sum(c["output"] for c in calls),
        "error": "" if done.status == 200 else json.dumps(done.body, ensure_ascii=False)[:300],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--model", default="", help="문제 넣기 테마의 모델:추론정도. 비우면 지금 설정")
    parser.add_argument("--per-theme", type=int, default=0, help="주제마다 앞에서 몇 문제만(0은 전부)")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.model:
        os.environ["ALGOBLOCK_THEME_INGEST"] = args.model
    problems, seen = [], defaultdict(int)
    for path in args.files:
        for row in json.loads(Path(path).read_text(encoding="utf-8")):
            seen[row["theme"]] += 1
            if not args.per_theme or seen[row["theme"]] <= args.per_theme:
                problems.append(row)
    jobs = [(problem, run) for run in range(1, args.runs + 1) for problem in problems]

    usage = _backend_session().usage  # app/llm의 app.llm.usage(호출마다 토큰을 적는 곳)

    def record(task, model, payload, seconds, **_):
        CALLS[NOW.get()].append({"task": task, "model": model, "seconds": round(seconds, 2), **usage.tokens(payload)})

    def safe(job):
        try:
            return copy_context().run(one, *job)
        except Exception as exc:  # noqa: BLE001 - 하나가 죽어도 나머지는 잰다
            return {"id": job[0]["id"], "run": job[1], "status": 0, "error": f"{type(exc).__name__}: {exc}"[:300]}

    with mock.patch.object(usage, "record", record), ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(safe, jobs))
    ok = [row for row in rows if row.get("planned")]
    times = [row["seconds"] for row in ok] or [0]
    models = sorted({call["model"] for calls in CALLS.values() for call in calls if call["task"] == "plan.solve"})
    summary = {
        "model": args.model or "지금 설정", "solve_models": models, "files": args.files, "plans": len(rows), "planned": len(ok),
        "verified": sum(row["verified"] for row in ok), "first_try": sum(row["first_try"] for row in ok),
        "solve_calls": sum(row["solve_calls"] for row in ok), "redrawn": sum(row["draft_calls"] > 1 for row in ok),
        "hint_calls": sum(row["hint_calls"] for row in ok), "blocks": sum(row["blocks"] for row in ok),
        "empty_hint_blocks": sum(row["empty_hint_blocks"] for row in ok), "seconds_median": statistics.median(times), "seconds_max": max(times),
        "input_tokens": sum(row["input_tokens"] for row in ok), "output_tokens": sum(row["output_tokens"] for row in ok),
        "failed": [(row["id"], row["run"], row.get("status"), row.get("checks"), row.get("error")) for row in rows if not row.get("verified")],
    }
    label = (models[0] if models else "none").split("/")[-1]
    out = Path(__file__).with_name("results") / f"ingest-{time.strftime('%Y%m%d-%H%M%S')}-{label}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(out)


if __name__ == "__main__":
    main()
