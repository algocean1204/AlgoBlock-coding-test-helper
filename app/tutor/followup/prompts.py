"""인용한 말과 그 스레드만. 메인 대화 전체와 다른 블록 코드는 넣지 않는다."""

from ..common.progress_view import active_plan, current_index
from ..common.talk_prompts import talk_system
from ..common.talk_rules import many_asks_line
from ..knowledge.ontology import skill_examples
from ..common.solution import solution_lines
from ..llm import cached_user
from ..request_check.nodes import mode_messages
from ..state import MainState

SYSTEM = talk_system("너는 코딩테스트 튜터다. 사용자가 스스로 풀이 순서를 떠올리고 코드를 직접 쓰게 돕는다.", basis=False)


def quote_context(state: MainState) -> dict:
    """N1 인용 문맥 모으기. 인용이 있는지는 A3이 이미 확인했다."""
    req = state["request"]
    quote = next(item for item in mode_messages(state) if item.id == req.quote_id)
    thread = next((item for item in state["ctx"].followups if item.quote_id == req.quote_id), None)
    said = [] if thread is None else thread.messages
    plan = active_plan(state)
    index = current_index(state)
    name = plan.blocks[index].name if plan is not None and 0 <= index < len(plan.blocks) else ""
    return {
        "quote": quote.text,
        "thread": [f"{'튜터' if m.role == 'service' else '사용자'}: {m.text}" for m in said],
        "block_name": name,
        "question": req.text or "",
        "mode": req.mode,
        "problem": state["ctx"].problem_text,
        "guide": solution_lines(state),
        "examples": skill_examples(state["ctx"].skills),
    }


def answer_messages(context: dict) -> list[dict]:
    guide = context.get("guide") or []
    lines = [f"문제:\n{context.get('problem', '')}", *guide, f"인용한 말:{context['quote']}", "이 인용에 대한 대화:", *(context["thread"] or ["없음"])]
    if context["block_name"]:
        lines.append(f"지금 블록:{context['block_name']}")
    lines += [
        f"질문:{context['question']}",
        *many_asks_line(context["question"]),
        "인용한 말, 위 대화, 문제 글만 보고 답한다. 문제 글의 사실은 작은따옴표로 인용하고 (문제 글)을, 짐작은 (추론)을 붙인다. "
        "문법을 물으면(코드로 어떻게 쓰는지, 문법을 모르겠다) 피하지 않고 답한다: 그 문법을 이 문제와 상관없는 작은 예(과일 이름, 점수 등 다른 변수 이름)로 한 줄 보여 주고 뜻을 한 문장으로 푼다. "
        "이 문제의 변수 이름으로 쓴 코드와 이 블록의 답 코드는 쓰지 않는다. 코드 블록(```)은 쓰지 않는다.",
        *(["참고 — 이 문제에서 자주 필요한 문법의 예(이 문제와 상관없는 변수로 쓴 것. 사용자가 그 문법을 물었을 때만 그대로 보여 줘도 된다):", *context["examples"]]
          if context.get("examples") else []),
        "문법도 아니고 인용과도 무관한 질문이면, 메인 대화에서 이어 가자고 한 문장으로 답한다.",
        "다음 블록으로 넘기지 않는다.",
        *(["지금 블록의 답(쓸 자료구조·기법 이름, 무엇을 키·값으로 둘지, 블록에서 정할 것)은 말하지 않는다. 사용자가 이미 말한 것만 되짚는다."]
          if context.get("mode") == "chair" else []),
        "쉬운 말로 3문장 이내. 끝은 사용자가 이어서 생각할 질문 하나로 맺는다.",
        "출력: 말풍선 글만.",
    ]
    return [{"role": "system", "content": SYSTEM}, cached_user(lines, 1 + len(guide))]
