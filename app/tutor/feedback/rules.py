"""피드백 검사. 확신 표시를 채우고, 힌트 머리를 맞추고, 금지 표현을 지운다. 코드 펜스는 거절한다."""

import re
from difflib import SequenceMatcher

from ..common.talk_rules import BANNED
from ..state import ErrorInfo

MARKS = ("[확실]", "[가능성 높음]", "[추측]")
_MARK = re.compile(r"^\[(확실|가능성 높음|추측)\]\s*")
_HIGH = re.compile(r"가능성이 높")
_GUESS = re.compile(r"일 수 있|로 보입니다|로 보여요")


_COUNTED = re.compile(r"\d+\s*(?:번째\s*줄|째\s*줄|번)")
_BLOCK = re.compile(r"블록\s*(\d+)")
_BLOCK_NAME = re.compile(r"블록\s*\d+(?:\([^)]*\))?")
SHARED = 6  # 수 없이 블록을 짚은 문장이 그 블록의 기록 줄과 이만큼(공백을 뺀 글자) 이어서 같아야 기록을 옮긴 것으로 본다


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _facts(line: str) -> list[tuple[str, str]]:
    """기록 줄의 센 사실 [(수, 수 앞의 낱말)]. 낱말은 마지막 구분(:, 쉼표, 따옴표, 괄호) 뒤의 마지막 세 낱말에서 끝 조사를 뗀 것('오답', '찾지 못한 답').
    줄 번호(…번째 줄)는 수가 곧 사실이라 낱말을 보지 않는다."""
    out = []
    for hit in _COUNTED.finditer(line):
        words = re.split(r"[:,'()]", line[:hit.start()])[-1].split()[-3:]
        key = "" if "줄" in hit.group() else re.sub(r"(이|가|은|는|을|를)$", "", "".join(words))
        out.append((_squash(hit.group()), key))
    return out


def recorded(body: str, record: str) -> bool | None:
    """문장이 기록의 사실을 옮겼는가. 센 수도 블록도 없으면 None.
    센 수가 있으면 문장의 수마다 기록 줄에 같은 수와 그 수 앞의 낱말이 함께 있어야 참이다('실행 오류가 2번'이 제출 기록의 '오답 2번' 덕에 [확실]이었다).
    문장이 블록을 짚으면 그 블록의 기록 줄만 본다. 수 없이 블록을 짚었으면 그 블록의 기록 줄과 SHARED자 넘게 이어서 같아야 참이다."""
    blocks = set(_BLOCK.findall(body))
    lines = [line for line in (record or "").splitlines() if not blocks or blocks & set(_BLOCK.findall(line))]
    hits = list(_COUNTED.finditer(body))
    if hits:
        facts = [fact for line in lines for fact in _facts(line)]
        # 수마다 그 수 바로 앞의 말(앞 수 뒤부터)에 기록의 같은 수의 낱말이 있어야 한다. 하나만 맞아도 참이면 '실행 오류가 2번, 오답이 1번'이 [확실]이었다
        starts = [0, *(hit.end() for hit in hits)]
        return all(any(count == _squash(hit.group()) and key in _squash(body[start:hit.start()]) for count, key in facts)
                   for hit, start in zip(hits, starts))
    if not blocks:
        return None
    rest = _squash(_BLOCK_NAME.sub("", body))
    return any(SequenceMatcher(None, rest, other, autojunk=False).find_longest_match(0, len(rest), 0, len(other)).size >= SHARED
               for other in (_squash(_BLOCK_NAME.sub("", line)) for line in lines))


def mark_claims(analysis: str, record: str = "") -> str:
    """주장 문장은 모두 확신 표시로 시작하고, 질문 문장에는 표시가 없다. 말끝이 표시와 어긋나면 말끝을 따르고, 표시 없는 주장에는 [추측].
    이번 풀이의 기록에 있는 수(…번, …번째 줄)를 그대로 옮긴 문장은 [확실]이다(센 사실에 [추측]이 붙었다).
    센 수나 블록을 짚었는데 기록과 맞지 않는 문장은 [확실]일 수 없다: [추측]."""
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
        if mark == "[확실]" and source is False:  # 센 수나 블록을 짚었는데 기록과 맞지 않는다
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
