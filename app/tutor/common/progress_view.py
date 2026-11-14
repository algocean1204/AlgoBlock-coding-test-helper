"""계획과 지금 블록 위치를 읽는다. 새 계획이 있으면 그것을, 없으면 저장된 계획을 본다."""

from ..save.respond import shown_count
from ..state import BlockPlan, MainState


def active_plan(state: MainState) -> BlockPlan | None:
    return state.get("plan") or state["ctx"].plan


def base_open_count(state: MainState) -> int:
    return 1 if state.get("plan") is not None else state["ctx"].open_count


def found_check(state: MainState) -> int | None:
    """의자에서 이미 찾은 블록(이름이 드러난 블록)이나 가이드의 앞 블록(지금 블록보다 앞)의 코드를 확인받는 턴이면 그 블록 번호, 아니면 None.
    이 턴은 진행(열린 블록 수)을 바꾸지 않는다. 통과한 앞 블록을 고쳐도 다시 확인할 길이 없었다."""
    req, ctx = state["request"], state["ctx"]
    if req.kind != "turn" or req.mode not in ("chair", "guide") or req.event != "block_filled" or ctx.plan is None or state.get("plan") is not None:
        return None
    index = next((i for i, b in enumerate(ctx.plan.blocks) if b.id == req.block_id), None)
    limit = shown_count(ctx, "chair") if req.mode == "chair" else ctx.open_count - 1
    return index if index is not None and index < limit else None


def current_index(state: MainState) -> int:
    """이번 턴이 겨눈 블록: 의자에서 찾은 블록의 코드 확인이면 그 블록, 아니면 지금 블록."""
    found = found_check(state)
    return base_open_count(state) - 1 if found is None else found
