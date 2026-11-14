"""피드백 노드: assess → pick_strategy → analyze → check_feedback(graph.py). 채점·전략은 블록 계획(plan)과 같이 쓴다."""

from ..common.assess import assess_node, pick_strategy_node
from ..common.progress_view import active_plan
from ..common.scope import algorithm_name
from ..llm import llm, model_name
from ..state import Analysis, MainState
from .prompts import analyze_messages, record_lines
from .rules import check_feedback as check_rule


def submitted_code(state: MainState) -> str:
    sub = state["ctx"].latest_submission
    return "" if sub is None else sub.source or ""


assess = assess_node("feedback.assess", submitted_code)
pick_strategy = pick_strategy_node(submitted_code)


def analyze(state: MainState) -> dict:
    return {"draft": llm(model_name()).use(analyze_messages(state), Analysis, task="feedback.analyze")}


def check_feedback(state: MainState) -> dict:
    written: Analysis = state["draft"]
    plan = active_plan(state)
    record = "\n".join(record_lines(state["ctx"], plan))
    fields, error = check_rule(written.analysis, written.similar_hint, written.advice, algorithm_name(plan.algorithm if plan else ""), record)
    if error:
        return {"error": error, "draft": None}
    sub = state["ctx"].latest_submission
    return {
        "result": {"submission_id": None if sub is None else sub.id, **fields, "strategy": state.get("strategy"), "score": state.get("score")},
        "draft": None,
    }
