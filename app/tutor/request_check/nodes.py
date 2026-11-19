"""A3 요청 검사. 첫 위반 하나만 오류로 남긴다. 거절이면 모델을 부르지 않는다. 기능 노드 안에는 검사가 없다."""

from ..common.progress_view import found_check
from ..state import KINDS, MainState, fail


def mode_messages(state: MainState):
    ctx = state["ctx"]
    return ctx.guide if state["request"].mode == "guide" else ctx.chair


def _current_block(state: MainState):
    plan = state["ctx"].plan
    index = state["ctx"].open_count - 1
    if plan is None or index < 0 or index >= len(plan.blocks):
        return None
    return plan.blocks[index]


def check_request(state: MainState) -> dict:
    kind = state["request"].kind
    if kind not in KINDS:
        return fail("validation", "알 수 없는 요청이에요. 화면을 새로 열고 다시 해 주세요.")
    return {"turn": _turn, "fill": _fill, "feedback": _feedback, "debug": _debug}.get(kind, lambda s: {})(state)


def _debug(state: MainState) -> dict:
    req = state["request"]
    if not (req.code or "").strip():
        return fail("validation", "코드를 먼저 적어 주세요.")
    if not isinstance(req.report, dict) or not req.report.get("status"):
        return fail("validation", "먼저 코드를 제출하거나 실행해 주세요.")
    if req.report.get("status") == "passed":
        return fail("validation", "이 코드는 통과했어요. 틀린 코드에서만 원인을 찾아요.")
    return {}


def _turn(state: MainState) -> dict:
    req = state["request"]
    if req.mode not in {"chair", "guide"}:
        return fail("validation", "푸는 방식이 맞지 않아요. 방식을 다시 골라 주세요.")
    if req.event not in {"start", "message", "block_filled", "next"}:
        return fail("validation", "알 수 없는 요청이에요. 화면을 새로 열고 다시 해 주세요.")
    if req.event == "start" and mode_messages(state):
        return fail("already_started", "이미 시작한 대화예요.")
    if req.event == "next":
        # 채우기로 열린 블록처럼 아직 첫 질문이 없는 지금 블록에만 쓴다
        index = state["ctx"].open_count - 1
        if index < 0 or any(m.role == "service" and m.block_index == index for m in mode_messages(state)):
            return fail("validation", "지금 블록에는 이미 질문이 있어요.")
    if req.event == "message" and not (req.text or "").strip():
        return fail("validation", "보낼 말을 적어 주세요.")
    if req.event == "block_filled":
        # 지금 블록, 또는 의자에서 이미 찾은 블록(found_check. 진행은 그대로)만 받는다
        current = _current_block(state)
        if not (req.code or "").strip() or ((current is None or req.block_id != current.id) and found_check(state) is None):
            return fail("validation", "이 블록에 코드를 적은 뒤 확인해 주세요.")
    return {}


def _fill(state: MainState) -> dict:
    plan = state["ctx"].plan
    ids = [] if plan is None else [block.id for block in plan.blocks]
    if state["request"].block_id not in ids:
        return fail("block_not_found", "이 문제에 없는 블록이에요. 화면을 새로 열고 다시 해 주세요.")
    if ids.index(state["request"].block_id) >= state["ctx"].open_count:
        return fail("block_closed", "아직 열리지 않은 블록이에요. 앞 블록부터 풀어 주세요.")
    return {}


def _feedback(state: MainState) -> dict:
    if state["ctx"].latest_submission is None:
        return fail("not_submitted", "코드를 한 번 제출한 뒤에 받을 수 있어요.")
    return {}
