"""모델 호출 기록(자료 폴더의 usage.jsonl)을 흐름별·과정(task)별로 묶어 호출 수, 토큰, 캐시 적중률, 어림 금액을 낸다.

python3 tutor/eval/cost.py <usage.jsonl> [--flows flows.jsonl]   (graph를 import하지 않아 langgraph 없이 돈다)
flows.jsonl은 한 줄에 {"flow": 이름, "start": 시각, "end": 시각}(time.time() 초). 기록의 at이 그 사이인 호출이 그 흐름이다.
캐시 적중률 = 캐시에서 읽은 입력 / 전체 입력(새 입력 + 캐시 읽기 + 캐시 쓰기).
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

# 백만 토큰당 달러 (새 입력, 캐시 쓰기 5분, 캐시 읽기, 출력).
# 출처: Anthropic 공개 가격표 https://platform.claude.com/docs/en/about-claude/pricing (2026-11-13 확인).
# Haiku 5.5는 프롬프트 10만 토큰 이하 값이다(넘으면 5배. 이 앱의 호출은 넘지 않는다). 1시간 캐시는 쓰지 않는다(ALGOBLOCK_LLM_CACHE_TTL 기본).
# OpenAI(gpt-6-luna 등)는 공개 가격표를 확인하지 못해 비운다(openai.com/api/pricing이 403). 금액 칸이 빈다.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.125, 0.01, 0.50),
    "claude-sonnet-5-5": (2.00, 2.50, 0.10, 10.00),
    "claude-opus-5-5": (4.00, 5.00, 0.20, 20.00),
}
PRICED_AT = "2026-11-13"
KEYS = ("input", "cache_read", "cache_write", "output")


def dollars(row: dict) -> float | None:
    name = str(row.get("model") or "")
    if name.startswith("cli/"):  # 개발용 연결(이 PC의 Claude Code): 구독으로 돌아 금액이 없다
        return 0.0
    price = PRICES.get(name.rpartition("/")[2])
    if price is None:
        return None
    new, write, read, out = price
    return (row["input"] * new + row["cache_write"] * write + row["cache_read"] * read + row["output"] * out) / 1_000_000


def summary(rows: list[dict]) -> dict:
    total = {key: sum(int(row.get(key) or 0) for row in rows) for key in KEYS}
    seen = total["input"] + total["cache_read"] + total["cache_write"]
    costs = [dollars({**{key: int(row.get(key) or 0) for key in KEYS}, "model": row.get("model")}) for row in rows]
    return {"calls": len(rows), "retries": sum(bool(row.get("retry")) for row in rows), **total,
            "hit": total["cache_read"] / seen if seen else 0.0, "seconds": round(sum(float(row.get("seconds") or 0) for row in rows), 1),
            "usd": None if any(cost is None for cost in costs) else sum(costs)}


def table(groups: dict[str, list[dict]], title: str) -> list[str]:
    out = [f"| {title} | 호출 | 다시 | 새 입력 | 캐시 읽기 | 캐시 쓰기 | 출력 | 캐시 적중 | 초 | 어림 $ |", "|---|---|---|---|---|---|---|---|---|---|"]
    for name, rows in [*groups.items(), ("합계", [row for rows in groups.values() for row in rows])]:
        s = summary(rows)
        usd = "" if s["usd"] is None else f"{s['usd']:.4f}"
        out.append(f"| {name} | {s['calls']} | {s['retries']} | {s['input']} | {s['cache_read']} | {s['cache_write']} | {s['output']} | {s['hit']:.0%} | {s['seconds']} | {usd} |")
    return out


def report(rows: list[dict], flows: list[dict] | None = None) -> str:
    lines = [f"단가: Anthropic 공개 가격표({PRICED_AT} 확인). 표에 없는 모델이 끼면 금액 칸을 비운다.", ""]
    if flows:
        by_flow = {flow["flow"]: [row for row in rows if flow["start"] <= row["at"] <= flow["end"]] for flow in flows}
        lines += table(by_flow, "흐름") + [""]
        for flow, picked in by_flow.items():
            by_task = defaultdict(list)
            for row in picked:
                by_task[row["task"] or "?"].append(row)
            lines += [f"### {flow}", *table(dict(by_task), "과정"), ""]
    else:
        by_task = defaultdict(list)
        for row in rows:
            by_task[row["task"] or "?"].append(row)
        lines += table(dict(by_task), "과정")
    return "\n".join(lines)


def read_lines(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--flows", default="")
    args = parser.parse_args()
    print(report(read_lines(args.log), read_lines(args.flows) if args.flows else None))


if __name__ == "__main__":
    main()
