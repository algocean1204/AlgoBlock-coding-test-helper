"""평가기 보정. 보정 세트(golden.py)에서 기준마다 정확도·카파·불확실 비율을 재고, 문턱을 넘은 기준만 믿는다(trusted).

믿지 않는 기준은 보고서에 '참고'로만 나오고 개선 루프의 판단(통과·실패)에 쓰지 않는다.
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

from .judge import CRITERIA, judge

MIN_N = 6
MIN_ACCURACY = 0.85
MIN_KAPPA = 0.6
MAX_UNCERTAIN = 0.15


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    """코언 카파. pairs=(정답, 평가기). 정답이 한 종류뿐이면 None."""
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    truth, guess = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    if len(truth) < 2:
        return None
    expected = sum(truth[label] * guess.get(label, 0) for label in truth) / (n * n)
    return round((observed - expected) / (1 - expected), 3) if expected < 1 else None


def score(results: list[dict]) -> dict:
    """results: [{"labels": 정답, "got": tally 결과}]. 기준마다 지표와 trusted."""
    table = {}
    for name in CRITERIA:
        pairs, uncertain, unstable = [], 0, 0
        for row in results:
            truth = row["labels"].get(name)
            if truth is None:
                continue
            got = row["got"][name]
            uncertain += got["label"] == "uncertain"
            unstable += got["agree"] < 1
            pairs.append((truth, got["label"]))
        n = len(pairs)
        accuracy = round(sum(a == b for a, b in pairs) / n, 3) if n else None
        k = kappa(pairs)
        trusted = (
            n >= MIN_N
            and accuracy is not None and accuracy >= MIN_ACCURACY
            and (k is None or k >= MIN_KAPPA)
            and uncertain / n <= MAX_UNCERTAIN
        )
        misses = [f"{row['id']}: 정답 {row['labels'][name]} / 평가기 {row['got'][name]['label']}"
                  for row in results if name in row["labels"] and row["labels"][name] != row["got"][name]["label"]]
        table[name] = {"n": n, "accuracy": accuracy, "kappa": k, "uncertain": uncertain, "unstable": unstable,
                       "trusted": trusted, "misses": misses}
    return table


def calibrate(cases: list[dict], k: int = 3, workers: int = 4, holdout: list[dict] = ()) -> dict:
    def one(c):
        return {"id": c["id"], "labels": c["labels"], "got": judge(c["item"], k=k)}

    everything = list(cases) + list(holdout)
    contexts = [copy_context() for _ in everything]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda pair: pair[0].run(one, pair[1]), zip(contexts, everything)))
    dev, held = score(results[: len(cases)]), score(results[len(cases) :])
    for name, row in dev.items():
        # 보류 세트(평가기를 고칠 때 안 본 사례)에서도 문턱을 넘어야 믿는다
        other = held.get(name) or {}
        row["holdout"] = {key: other.get(key) for key in ("n", "accuracy", "kappa", "misses")}
        if other.get("n"):
            row["trusted"] = row["trusted"] and other["accuracy"] >= MIN_ACCURACY
    return {"criteria": dev, "results": results}
