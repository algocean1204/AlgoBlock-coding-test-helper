"""피드백 노드: assess → pick_strategy → analyze → check_feedback(graph.py). 채점·전략은 블록 계획(plan)과 같이 쓴다."""

import logging

from ..common.assess import assess_node, pick_strategy_node
from ..common.progress_view import active_plan
from ..common.scope import algorithm_name
from ..debug.rules import trap_in_code, trap_of
from ..llm import llm, model_name
from ..state import Analysis, MainState
from .prompts import analyze_messages, record_lines, used_blocks
from ..common.talk_rules import sentences, shape_problems, tidy
from .rules import check_feedback as check_rule

LOG = logging.getLogger("graph.shape")  # 긴 글의 꼴을 어긴 곳(평가기가 모은다. 다시 부르지 않는다)


def submitted_code(state: MainState) -> str:
    sub = state["ctx"].latest_submission
    return "" if sub is None else sub.source or ""


assess = assess_node("feedback.assess", submitted_code)
pick_strategy = pick_strategy_node(submitted_code)


def analyze(state: MainState) -> dict:
    return {"draft": llm(model_name()).use(analyze_messages(state), Analysis, task="feedback.analyze")}


def check_feedback(state: MainState) -> dict:
    written: Analysis = state["draft"]
    written = Analysis(tidy(written.analysis), tidy(written.similar_hint), tidy(written.advice))
    found = shape_problems("\n- ".join(sentences(written.analysis)))  # 화면은 문장마다 한 항목이다
    if found:
        LOG.info("긴 글 꼴", extra={"where": "feedback.analysis", "problems": found})
    plan = active_plan(state)
    record = "\n".join(record_lines(state["ctx"], plan))
    fields, error = check_rule(written.analysis, written.similar_hint, written.advice, algorithm_name(plan.algorithm if plan else ""), record,
                                opened=state["ctx"].open_count if used_blocks(state["ctx"]) else 0)
    if error:
        return {"error": error, "draft": None}
    sub = state["ctx"].latest_submission
    note = trap_note(state["ctx"], sub)
    if note:
        fields["advice"] = f"{fields['advice']} {note}".strip()
    # 통과한 제출에는 전략을 넘기지 않는다: 화면이 전략 제목('정석 순서로 다시 짜 보기')이 아니라 기본 제목을 쓴다
    strategy = None if sub is not None and sub.ok else state.get("strategy")
    return {
        "result": {"submission_id": None if sub is None else sub.id, **fields, "strategy": strategy, "score": state.get("score")},
        "draft": None,
    }


def trap_note(ctx, sub) -> str:
    """디버그가 고른 언어 함정의 정해진 글(모델이 다시 쓰지 않는다). 저장된 제출에는 케이스별 결과가 없어 피드백이 스스로 고르지 않는다.
    실패한 제출이면 그 코드가 아직 그 함정의 꼴일 때만 무슨 일이 일어나는지(what).
    통과한 제출이면 그 꼴을 고친 흔적이 있을 때만(이제 함정의 꼴이 아니다) what과 고치는 법(fix): 고른 함정은 문제에 남아, 다른 방식으로 통과한 제출에도 붙을 수 있었다.
    고른 것이 없으면 빈 글."""
    trap = trap_of(ctx.traps, ctx.debug_state.trap if ctx.debug_state is not None else "")
    if trap is None or sub is None or sub.ok == trap_in_code(trap, sub.source):
        return ""
    return f"{trap['what']} {trap['fix']}" if sub.ok else trap["what"]
