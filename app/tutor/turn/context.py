"""N1 턴 준비."""

from ..common.progress_view import active_plan, current_index
from ..common.talk_rules import FILL_TIP
from ..request_check.nodes import mode_messages
from ..state import MainState, TurnContext, fail


def prepare(state: MainState) -> dict:
    plan = active_plan(state)
    if plan is None or not plan.blocks:
        return fail("invalid_output", "계획이 없습니다.")
    index = current_index(state)
    if not 0 <= index < len(plan.blocks):
        return fail("invalid_output", "지금 블록이 없습니다.")
    said = mode_messages(state)
    # 사용자 방법으로 다시 짠 뒤에는 그 표시(replan) 뒤의 말만 본다. 이번 요청에서 다시 짰으면 본 말이 없다
    cut = max((i for i, m in enumerate(said) if m.role == "service" and m.move == "replan"), default=-1)
    replanned = state.get("replanned")
    here = [] if replanned == "followed" else [m for m in said[max(cut, 0):] if m.block_index == index]
    service = [m for m in here if m.role == "service"]
    req = state["request"]
    turn = TurnContext(
        index=index,
        block=plan.blocks[index],
        last_question=service[-1].text if service else "없음",
        recent=[f"{'튜터' if m.role == 'service' else '사용자'}: {m.text}" for m in here][-4:],
        moves_used=[m.move for m in service if m.move],
        event="replan" if replanned == "followed" else (req.event or ""),
        text=(req.text or "").strip(),
        followed_before=cut >= 0 or replanned is not None,
        basis_asked=any(m.role == "service" and m.move == "basis" for m in said[max(cut, 0):]),
        previous=next((m.text for m in reversed(here) if m.role == "user"), ""),
        tipped=any(FILL_TIP in m.text for m in service),
        hints_seen=sum(bool(h.strip()) and any(h.strip() in m.text for m in service) for h in plan.blocks[index].hints),
    )
    return {"turn": turn}
