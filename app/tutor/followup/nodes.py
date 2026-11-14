"""A8 노드. N1 gather, N2 answer, N3 check_reply. 넘김(advance)은 만들지 않는다."""

from ..common.progress_view import active_plan, current_index
from ..common.talk_rules import FALLBACK, note_fallback, repair, reply_problems
from ..llm import llm, model_name
from ..state import MainState
from .prompts import answer_messages, quote_context


def gather(state: MainState) -> dict:
    return {"draft": quote_context(state)}


def answer(state: MainState) -> dict:
    text = llm(model_name()).use(answer_messages(state["draft"]), None, task="followup.answer")
    return {"reply_draft": (text or "").strip()}


def check_reply(state: MainState) -> dict:
    plan = active_plan(state)
    index = current_index(state)
    later = [b.name for b in plan.blocks[index + 1 :]] if plan else []
    reference = plan.blocks[index].reference if plan and 0 <= index < len(plan.blocks) else ""
    text = state.get("reply_draft") or ""
    draft = state.get("draft") or {}
    said = "\n".join([draft.get("quote", ""), draft.get("question", ""), *(draft.get("thread") or [])])
    problem = state["ctx"].problem_text
    language = state["ctx"].language
    found = reply_problems(text, move="followup", problem=problem, reference=reference, later_names=later, said=said, language=language)
    if not found or not {"코드 펜스", "참고 코드", "뒤 블록 이름", "금지 표현", "동의로 시작", "3인칭 메모", "영어 지시문"} & set(found):
        text = repair(text, problem, said, "followup", reference, language)  # 고칠 수 있는 위반은 고쳐서 보낸다
        found = reply_problems(text, move="followup", problem=problem, reference=reference, later_names=later, said=said, language=language)
    if found:
        note_fallback("followup", found, text)
        text = FALLBACK["followup"]
    return {"result": {"reply": text, "move": "followup"}, "draft": None}
