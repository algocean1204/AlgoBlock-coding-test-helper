"""평가기 1층: 규칙 검사. 모델을 부르지 않아 같은 입력이면 늘 같은 결과다(신뢰의 바닥).

기록(transcript)의 한 줄 = 요청 하나. 튜터 말이 있는 줄(turn, followup)마다 말풍선 검사를 하고,
세션 전체로 진행·막힘·대체 질문·반복·오류·시간·캐시 지표를 낸다.
"""

import re
import statistics

from ..common.talk_rules import _ENGLISH, _NOTE, FALLBACK, KIND_LABEL, banned_in, quotes_ok, sentence_count, without_problem_quotes

CHAT_KINDS = ("turn", "followup", "debug")


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def is_fallback(reply: str, move: str | None) -> bool:
    """규칙 위반으로 정해진 대체 질문이 나갔는가(앞말·이음말은 떼고 본다)."""
    if move == "close":
        return False  # 마침 말은 일부러 고정한 말이다
    fixed = FALLBACK.get(move or "")
    return bool(fixed) and _norm(reply).endswith(_norm(fixed))


def reply_flags(row: dict, previous_reply: str | None) -> list[str]:
    """튜터 말 하나의 위반 목록. 비면 통과."""
    reply = row.get("reply") or ""
    hidden = row.get("hidden") or {}
    problem = row.get("problem", "")
    flags = []
    if not reply.strip():
        return ["빈 말"]
    if "```" in reply:
        flags.append("코드 펜스")
    if banned_in(reply, problem):
        flags.append("금지 표현")
    if sentence_count(reply) > 3:
        flags.append("3문장 초과")
    if row["kind"] in ("turn", "debug") and not reply.rstrip().endswith(("?", "？")):
        flags.append("질문으로 안 끝남")
    for line in (hidden.get("reference") or "").splitlines():
        if len(_norm(line)) >= 5 and line.strip() in reply:
            flags.append("참고 코드 유출")
            break
    if any(name and name in reply for name in hidden.get("later_names") or []):
        flags.append("뒤 블록 이름")
    said = "\n".join([problem, row.get("user") or "", *(row.get("context") or []), row.get("quote") or "", row.get("code") or "", *KIND_LABEL.values()])
    if not quotes_ok(reply, problem, said):  # 문제 글이나 사용자 말·앞 대화에 있는 구절만 인용할 수 있다
        flags.append("문항에 없는 인용")
    plain = without_problem_quotes(reply, said)
    if _NOTE.search(plain) or _ENGLISH.search(plain):
        flags.append("모델 메모 유출")
    if is_fallback(reply, row.get("move")):
        flags.append("대체 질문")
    if previous_reply is not None and _norm(reply) == _norm(previous_reply):
        flags.append("직전과 같은 말")
    return flags


def annotate(rows: list[dict]) -> list[dict]:
    """줄마다 flags를 붙인다. 직전 말 비교는 같은 모드 안에서만."""
    last: dict[str, str] = {}
    for row in rows:
        if row["kind"] in CHAT_KINDS and row.get("status") == 200:
            key = f"{row['kind']}:{row.get('mode')}"
            row["flags"] = reply_flags(row, last.get(key))
            last[key] = row.get("reply") or ""
    return rows


def stuck_streak(rows: list[dict]) -> int:
    """같은 블록에서 넘어가지 못한 사용자 말이 연속으로 가장 길게 이어진 수."""
    best = streak = 0
    for row in rows:
        if row["kind"] == "fill" or row.get("event") == "next" or (row.get("event") == "block_filled" and row.get("advance")):
            streak = 0  # 채우기나 블록 코드 확인으로 넘어갔으면 새 블록에서 다시 센다
            continue
        if row["kind"] != "turn" or row.get("event") != "message":
            continue
        if row.get("advance"):
            streak = 0
        else:
            streak += 1
            best = max(best, streak)
    return best


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def session_metrics(rows: list[dict], calls: list[dict]) -> dict:
    """세션 하나의 지표. calls는 app.llm.usage 기록(모델 호출 단위)."""
    chat = [r for r in rows if r["kind"] in CHAT_KINDS and r.get("status") == 200]
    flagged = [r for r in chat if r.get("flags")]
    count = lambda name: sum(name in r.get("flags", []) for r in chat)  # noqa: E731
    seconds = [r["seconds"] for r in rows if "seconds" in r]
    final = next((r for r in reversed(rows) if r.get("open_count") is not None), {})
    read = sum(c.get("cache_read", 0) for c in calls)
    write = sum(c.get("cache_write", 0) for c in calls)
    fresh = sum(c.get("input", 0) for c in calls)
    submit = next((r for r in reversed(rows) if r["kind"] == "submit"), None)
    return {
        "requests": len(rows),
        "errors": [f"{r['kind']}:{r.get('status')}:{r.get('error_code')}" for r in rows if r.get("status") not in (None, 200)],
        "tutor_replies": len(chat),
        "clean_reply_rate": round(1 - len(flagged) / len(chat), 3) if chat else None,
        "fallback": count("대체 질문"),
        "repeat": count("직전과 같은 말"),
        "leak": count("참고 코드 유출") + count("뒤 블록 이름"),
        "fake_quote": count("문항에 없는 인용"),
        "banned": count("금지 표현"),
        "blocks_total": final.get("blocks_total"),
        "blocks_open": final.get("open_count"),
        "user_turns": sum(1 for r in rows if r["kind"] == "turn" and r.get("event") == "message"),
        "max_stuck": stuck_streak(rows),
        "fills": sum(1 for r in rows if r["kind"] == "fill" and r.get("status") == 200),
        "submits": sum(1 for r in rows if r["kind"] == "submit"),
        "debug_turns": sum(1 for r in rows if r["kind"] == "debug" and r.get("status") == 200),
        "replanned": any(r.get("move") == "replan" for r in rows),
        "submitted_ok": None if submit is None else submit.get("ok"),
        "feedback": any(r["kind"] == "feedback" and r.get("status") == 200 for r in rows),
        "explain": any(r["kind"] == "explain" and r.get("status") == 200 for r in rows),
        "latency_p50": round(statistics.median(seconds), 1) if seconds else None,
        "latency_p95": round(percentile(seconds, 0.95), 1) if seconds else None,
        "llm_calls": len(calls),
        "cache_hit_rate": round(read / (read + write + fresh), 3) if (read + write + fresh) else None,
    }
