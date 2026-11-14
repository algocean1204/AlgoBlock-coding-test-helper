"""A11 노드. N1 guard(펜스 검사), N2 progress(열린 블록 수)."""

from ..common.progress_view import active_plan, base_open_count
from ..state import MainState, fail


def strip_fence(text: str) -> str:
    body = (text or "").strip()
    if not body.startswith("```"):
        return body
    lines = body.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def guard(state: MainState) -> dict:
    result = dict(state.get("result") or {})
    kind = state["request"].kind
    if kind in {"turn", "followup", "debug"} and "```" in (result.get("reply") or "") and not result.pop("boxed", False):
        return fail("invalid_output", "말풍선에 코드 펜스가 있습니다.")
    if kind == "followup":
        result.pop("advance", None)
    if kind == "feedback" and "```" in (result.get("similar_hint") or ""):
        return fail("invalid_output", "힌트에 코드 펜스가 있습니다.")
    if kind == "fill":
        code = result.get("code") or ""
        if code.lstrip().startswith("```"):  # 펜스가 있을 때만 벗긴다. strip이 첫 줄 들여쓰기를 지운다
            code = strip_fence(code)
        if not code.strip():
            return fail("invalid_output", "블록 코드가 비었습니다.")
        result["code"] = code
    return {"result": result}


def progress(state: MainState) -> dict:
    plan = active_plan(state)
    if plan is None or not plan.blocks:
        return {"open_count": state["ctx"].open_count}
    total = len(plan.blocks)
    count = max(0, min(base_open_count(state), total))
    if count >= total:
        return {"open_count": total}
    result = state.get("result") or {}
    kind = state["request"].kind
    if kind == "turn" and result.get("advance"):
        count = total if state["request"].own_way and state["request"].skip else count + 1  # 끝까지 내 방식으로 쓰기: 남은 블록을 모두 연다
    elif kind == "fill" and count > 0 and state["request"].block_id == plan.blocks[count - 1].id:
        count += 1
    return {"open_count": min(count, total)}
