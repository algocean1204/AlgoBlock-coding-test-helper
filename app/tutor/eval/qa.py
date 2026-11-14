"""QA 실행기: 평가기 보정, 초보자 시나리오 실행, 규칙 검사 + 모델 평가기, 보고서.

app에서:
  python3 -m tutor.eval.qa calibrate [--cli] [--k 3]
  python3 -m tutor.eval.qa run [--cli] [--scenarios hash_library,...] [--modes chair,guide] [--k 3]
--cli 는 API 키 대신 이 PC의 Claude Code(claude -p)로 튜터·초보자·평가기를 돌린다(cli_client.py).
결과: eval/results/ 아래 calibration-*.json, qa-*.jsonl(기록), qa-*.md(보고서). 보고서는 가장 최근 보정의 trusted 기준만 판단에 쓴다.
"""

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context
from datetime import datetime
from pathlib import Path

from ..llm import use_llm
from .calibrate import calibrate
from .checks import CHAT_KINDS, annotate, session_metrics
from .drive import play, play_debug
from .golden import GOLDEN, HOLDOUT, HUMAN
from .judge import CRITERIA, judge
from .scenarios import all_scenarios

RESULTS = Path(__file__).resolve().parent / "results"


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def latest_calibration() -> dict | None:
    files = sorted(RESULTS.glob("calibration-*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def cmd_calibrate(k: int) -> dict:
    out = calibrate(GOLDEN + HUMAN, k=k, holdout=HOLDOUT)
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"calibration-{stamp()}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, row in out["criteria"].items():
        mark = "믿음" if row["trusted"] else "참고만"
        h = row["holdout"]
        print(f"{name:11} n={row['n']:2} 정확도={row['accuracy']} 카파={row['kappa']} 불확실={row['uncertain']} 흔들림={row['unstable']}"
              f" | 보류 n={h['n']} 정확도={h['accuracy']} → {mark}")
        for miss in row["misses"] + (h["misses"] or []):
            print(f"    {miss}")
    print(path)
    return out


def judge_item(row: dict) -> dict:
    hidden = row.get("hidden") or {}
    return {
        "problem": row["problem"], "mode": row["mode"],
        "block": {k: hidden.get(k) for k in ("name", "goal", "checks", "reference")},
        "context": row.get("context") or [], "user": row.get("user"),
        "decision": row.get("decision"), "reply": row.get("reply") or "", "code": row.get("code") if row["kind"] == "debug" else None,
        "judged": {k: (row.get("judged") or {}).get(k) for k in ("name", "goal", "checks")} if row.get("judged") else None,
    }


def play_one(scenario, mode, k):
    """mode: chair, guide, 또는 bug:<이름>(debug_bench.BUGS의 틀린 코드로 디버깅만)."""
    if mode.startswith("bug:"):
        from .debug_bench import BUGS

        session = play_debug(scenario, next(b[3] for b in BUGS if b[0] == mode[4:]))
    else:
        session = play(scenario, mode)
    rows = annotate(session.rows)
    targets = [r for r in rows if r["kind"] in CHAT_KINDS and r.get("status") == 200 and r.get("hidden")]
    contexts = [copy_context() for _ in targets]
    with ThreadPoolExecutor(max_workers=3) as pool:
        verdicts = list(pool.map(lambda pair: pair[0].run(judge, judge_item(pair[1]), k), zip(contexts, targets)))
    for row, got in zip(targets, verdicts):
        row["judge"] = got
    session.close()
    return session, rows


def summarize(name: str, rows: list[dict], calls: list[dict], trusted: dict) -> dict:
    metrics = session_metrics(rows, calls)
    judged = [r for r in rows if r.get("judge")]
    for crit in CRITERIA:
        labels = [r["judge"][crit]["label"] for r in judged]
        fails = labels.count("fail")
        counted = sum(label in ("pass", "fail") for label in labels)
        metrics[f"j_{crit}_fail"] = fails
        metrics[f"j_{crit}_rate"] = round(1 - fails / counted, 3) if counted else None
        metrics[f"j_{crit}_trusted"] = trusted.get(crit, False)
    metrics["session"] = name
    return metrics


def report(summaries: list[dict], rows_by: dict[str, list[dict]], trusted: dict) -> str:
    keys = ["blocks_open", "blocks_total", "user_turns", "max_stuck", "fills", "submitted_ok", "submits", "debug_turns", "replanned", "fallback", "repeat", "leak",
            "fake_quote", "banned", "clean_reply_rate", "latency_p50", "latency_p95", "cache_hit_rate", "errors"]
    lines = ["# QA 보고서", "", f"- 평가기 믿는 기준: {', '.join(c for c, ok in trusted.items() if ok) or '없음(보정 전)'}", ""]
    lines += ["| 지표 | " + " | ".join(s["session"] for s in summaries) + " |", "| --- |" + " --- |" * len(summaries)]
    for key in keys + [f"j_{c}_rate" for c in CRITERIA]:
        label = key + ("" if not key.startswith("j_") else (" (믿음)" if trusted.get(key[2:-5]) else " (참고)"))
        lines.append(f"| {label} | " + " | ".join(str(s.get(key)) for s in summaries) + " |")
    lines += ["", "## 실패 사례(평가기 다수결 fail 또는 규칙 위반)", ""]
    for name, rows in rows_by.items():
        for i, r in enumerate(rows):
            bad = [c for c, v in (r.get("judge") or {}).items() if v["label"] == "fail"]
            if r.get("flags") or bad:
                lines.append(f"- {name} #{i} [{r['kind']}/{r.get('move')}] 사용자: {r.get('user')!s:.60} → 튜터: {r.get('reply')!s:.120}")
                lines.append(f"  - 규칙: {', '.join(r.get('flags') or []) or '-'} / 평가기 fail: {', '.join(bad) or '-'}")
                for c in bad:
                    lines.append(f"    - {c}: {'; '.join(r['judge'][c]['reasons'])}")
    return "\n".join(lines)


def cmd_run(ids: list[str], modes: list[str], k: int, client) -> None:
    cal = latest_calibration()
    trusted = {name: row["trusted"] for name, row in (cal or {}).get("criteria", {}).items()}
    picked = [s for s in all_scenarios() if not ids or s.id in ids]
    jobs = [(s, m) for s in picked for m in modes if not m.startswith("bugs")]
    if "bugs" in modes:
        from .debug_bench import BUGS
        from .scenarios import by_id

        known = {s.id for s in all_scenarios()}  # 시나리오가 지금 없으면 그 버그는 건너뛴다
        jobs += [(by_id(b[1]), f"bug:{b[0]}") for b in BUGS if b[1] in known and (not ids or b[1] in ids)]
    out: dict[str, tuple] = {}

    def job(pair):
        scenario, mode = pair
        threading.current_thread().name = f"{scenario.id}:{mode}"
        out[f"{scenario.id}:{mode}"] = play_one(scenario, mode, k)

    contexts = [copy_context() for _ in jobs]
    with ThreadPoolExecutor(max_workers=min(len(jobs), 8)) as pool:
        list(pool.map(lambda pair: pair[0].run(job, pair[1]), zip(contexts, jobs)))
    calls = getattr(client, "calls", [])
    summaries, rows_by = [], {}
    for name, (_, rows) in sorted(out.items()):
        mine = [c for c in calls if c.get("thread") == name and not c["task"].startswith("eval.")]
        summaries.append(summarize(name, rows, mine, trusted))
        rows_by[name] = rows
    RESULTS.mkdir(exist_ok=True)
    at = stamp()
    with (RESULTS / f"qa-{at}.jsonl").open("w", encoding="utf-8") as file:
        for name, rows in rows_by.items():
            for r in rows:
                file.write(json.dumps({"session": name, **r}, ensure_ascii=False, default=str) + "\n")
    text = report(summaries, rows_by, trusted)
    (RESULTS / f"qa-{at}.md").write_text(text, encoding="utf-8")
    (RESULTS / f"qa-{at}-summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=1), encoding="utf-8")
    print(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["calibrate", "run"])
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--scenarios", default="")
    parser.add_argument("--modes", default="chair")
    args = parser.parse_args(argv)
    client = None
    if args.cli:
        from .cli_client import ClaudeCli

        client = ClaudeCli()
    with use_llm(client) if client else nullcontext():
        if args.command == "calibrate":
            cmd_calibrate(args.k)
        else:
            cmd_run([x for x in args.scenarios.split(",") if x], args.modes.split(","), args.k, client)
    return 0


if __name__ == "__main__":
    sys.exit(main())
