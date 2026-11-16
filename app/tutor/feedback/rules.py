"""피드백 검사. 확신 표시를 채우고, 힌트 머리를 맞추고, 금지 표현을 지운다. 코드 펜스는 거절한다."""

import re

from ..common.talk_rules import BANNED
from ..state import ErrorInfo

MARKS = ("[확실]", "[가능성 높음]", "[추측]")
_MARK = re.compile(r"^\[(확실|가능성 높음|추측)\]\s*")
_HIGH = re.compile(r"가능성이 높")
_GUESS = re.compile(r"일 수 있|로 보입니다|로 보여요")


_COUNTED = re.compile(r"\d+\s*(?:번째\s*줄|째\s*줄|번)")
_BLOCK = re.compile(r"블록\s*(\d+)")


def _counts(text: str) -> set[str]:
    return {re.sub(r"\s+", "", hit) for hit in _COUNTED.findall(text or "")}


def recorded(body: str, record: str) -> bool | None:
    """문장이 기록의 센 사실을 옮겼는가. 센 수가 없으면 None. 문장이 블록을 짚으면 그 블록의 기록 줄에 같은 수가 있어야 참이다
    (기록에 없는 '블록 1에서 넘어가지 못한 답 2번'이 다른 줄의 '2번' 덕에 [확실]이 되었다)."""
    counts = _counts(body)
    if not counts:
        return None
    blocks = set(_BLOCK.findall(body))
    return any(counts & _counts(line) and (not blocks or blocks & set(_BLOCK.findall(line))) for line in (record or "").splitlines())


def mark_claims(analysis: str, record: str = "") -> str:
    """주장 문장은 모두 확신 표시로 시작하고, 질문 문장에는 표시가 없다. 말끝이 표시와 어긋나면 말끝을 따르고, 표시 없는 주장에는 [추측].
    이번 풀이의 기록에 있는 수(…번, …번째 줄)를 그대로 옮긴 문장은 [확실]이다(센 사실에 [추측]이 붙었다).
    블록을 짚어 센 수를 말했는데 기록에 없는 문장은 [확실]일 수 없다: [추측]."""
    out = []
    for part in [p.strip() for p in re.split(r"(?<=[.?!？])\s+", (analysis or "").strip()) if p.strip()]:
        found = _MARK.match(part)
        body = part[found.end():] if found else part
        if not body.strip():  # 표시만 있고 문장이 없다
            continue
        if body.rstrip().endswith(("?", "？")):
            out.append(body)
            continue
        source = recorded(body, record)
        if source:
            out.append(f"[확실] {body}")
            continue
        mark = "[가능성 높음]" if _HIGH.search(body) else "[추측]" if _GUESS.search(body) else (found.group(0).strip() if found else "[추측]")
        if mark == "[확실]" and source is False and _BLOCK.search(body):
            mark = "[추측]"
        out.append(f"{mark} {body}")
    return " ".join(out)


def strip_banned(text: str) -> str:
    for word in BANNED:
        text = text.replace(word, "")
    return re.sub(r"\s{2,}", " ", text).strip()


def check_feedback(analysis: str, hint: str, advice: str, algorithm_name: str, record: str = "") -> tuple[dict, ErrorInfo | None]:
    if "```" in (hint or "") or "```" in (advice or ""):
        return {}, ErrorInfo("invalid_output", "힌트에 코드 펜스가 있습니다.")
    hint = strip_banned(hint or "")
    if algorithm_name and not hint.startswith(f"{algorithm_name}:"):
        hint = f"{algorithm_name}: {hint}"
    return {"analysis": mark_claims(strip_banned(analysis or ""), record), "similar_hint": hint, "advice": strip_banned(advice or "")}, None
