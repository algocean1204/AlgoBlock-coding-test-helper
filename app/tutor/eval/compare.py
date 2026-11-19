"""두 QA 실행 기록을 같은 규칙 검사로 다시 세어 나란히 놓는다(규칙 검사를 고친 뒤에도 전·후를 같은 잣대로 본다).

python3 -m tutor.eval.compare results/qa-A.jsonl results/qa-B.jsonl
모델 평가기 판정은 기록에 남은 것을 그대로 쓴다. 칸(parts)이 없는 옛 기록은 칸 기준을 재지 않는다(slot_clean_rate가 None).
"""

import json
import sys
from collections import defaultdict

from .checks import annotate
from .judge import CRITERIA

KEYS = ("blocks_open", "user_turns", "max_stuck", "fills", "submitted_ok", "clean_reply_rate", "slot_clean_rate", "fake_quote", "leak", "latency_p50")


def load(path: str) -> dict[str, list[dict]]:
    by = defaultdict(list)
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        row.pop("flags", None)
        by[row.pop("session")].append(row)
    return by


def numbers(rows: list[dict]) -> dict:
    from .checks import session_metrics

    rows = annotate(rows)
    out = {k: v for k, v in session_metrics(rows, []).items() if k in KEYS}
    judged = [r["judge"] for r in rows if r.get("judge")]
    for crit in CRITERIA:
        labels = [j[crit]["label"] for j in judged]
        counted = sum(label in ("pass", "fail") for label in labels)
        out[f"j_{crit}"] = round(1 - labels.count("fail") / counted, 3) if counted else None
    return out


def main(argv: list[str]) -> int:
    runs = [load(path) for path in argv]
    sessions = sorted(set().union(*runs))
    for name in sessions:
        print(f"\n## {name}")
        cols = [numbers(run[name]) if name in run else {} for run in runs]
        for key in [*KEYS, *(f"j_{c}" for c in CRITERIA)]:
            print(f"{key:18}" + " | ".join(f"{str(col.get(key)):>8}" for col in cols))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
