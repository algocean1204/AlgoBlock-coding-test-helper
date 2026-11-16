"""디버그 프롬프트. 진단(보이지 않음), 원인 판정, 질문."""

from ..common.scope import OUTSIDE_PROBLEMS
from ..common.talk_prompts import NOT_SAID
from ..common.talk_rules import BANNED, many_asks_line
from ..feedback.prompts import FAIL_WORD
from ..knowledge.ontology import size_rule, skill_examples
from ..common.solution import solution_lines
from ..llm import cached_user
from ..state import MainState
from .rules import error_tail, numbered, symptom

LOCATE_SYSTEM = (
    "너는 코딩테스트 튜터의 디버깅 진단자다. 코딩테스트를 막 시작한 사용자의 코드에서 지금 실패를 일으키는 원인 한 군데를 찾는다. "
    "이 진단은 사용자에게 보이지 않고, 튜터가 질문을 고르는 데만 쓴다."
)

SPEAK_SYSTEM = "\n".join(
    [
        "너는 코딩테스트 튜터의 생각하는 의자다. 사용자가 자기 코드의 틀린 곳을 스스로 찾게 디버깅을 돕는다.",
        "원칙:",
        "- 고친 코드를 대신 쓰지 않는다. 고친 줄과 무엇으로 바꿀지는 말하지 않는다. 사용자가 찾아서 직접 고친다.",
        "- 디버깅하는 법을 익히게 한다: 실패한 입력 하나를 고르고, 값을 한 줄씩 따라가고, 기대한 값과 실제 값을 견준다.",
        "- 사용자의 풀이 방향은 바꾸지 않는다. 지금 코드가 왜 다르게 도는지만 본다.",
        f"- 생각을 닫는 말을 쓰지 않는다: {', '.join(BANNED)}.",
        f"- {OUTSIDE_PROBLEMS}",
        "- 사용자의 말을 되풀이하거나 요약하는 문장으로 시작하지 않는다. 첫 문장부터 가정·빠진 경우·근거를 겨눈다.",
        f"- {NOT_SAID}",
        "- 사용자가 물은 것이 있으면 먼저 한 문장으로 받는다. 정답 코드를 달라고 하면 코드는 직접 써야 손에 남는다고 짧게 말하고, 지금 질문을 더 쉽게 바꿔 묻는다.",
        "쉬운 말로 한국어 1~3문장. 상대에게 직접 하는 말만 쓰고('사용자', '여러분'이라 부르지 않는다) 물음표로 끝나는 질문 하나로 끝낸다. 코드 블록을 쓰지 않는다.",
    ]
)

STEP_TEXT = {
    "symptom": "사용자가 방금 한 말이나 고친 것을 한마디로 받고, 지금 실패하는 입력과 기대한 값·실제 값을 알려 준 뒤, "
               "그 입력과 코드에서 바로 보이는 단서 하나(입력의 어떤 값·순서, 코드에서 그 값을 다루는 부분)를 짚어 살펴보게 묻는다. 원인과 줄 번호는 말하지 않는다.",
    "fix": "사용자가 원인을 짚었다. 그 말을 받아 주되 '맞아요' 같은 판정 낱말은 쓰지 않는다. 질문 속에 원인이 있는 줄 번호(진단의 줄)를 넣어 그 줄을 짚어 준다. 그 줄이 해야 할 일을 말로 한 문장 써 보게 하거나, 어떻게 바꿀지 묻는다. "
           "사용자가 고치는 문법을 모르겠다고 했으면 같은 문법을 이 문제와 상관없는 예(과일, 점수 등)로 한 줄 보여 준다. 고친 줄은 쓰지 않는다.",
    "trace": "실패한 입력으로, 원인 줄 근처의 변수 값이 어떻게 바뀌는지 따라가 보게 묻는다. 어떤 변수를 반복의 몇 번째에서 볼지 짚어 준다. 줄 번호와 원인은 말하지 않는다.",
    "line": "원인이 있는 줄 번호를 알려 주고, 실패한 입력에서 그 줄이 실제로 하는 일과 문제가 요구하는 일을 견주게 묻는다. 어떻게 고칠지는 말하지 않는다.",
    "cause": "무엇이 왜 틀렸는지 말로 설명한다. 코드는 쓰지 않는다. 그러면 그 줄을 어떻게 바꾸면 될지 묻는다.",
    "error": "오류 메시지가 보통 무슨 뜻인지 쉬운 말로 풀어 주고 몇 번째 줄인지 알려 준다. 이 코드에서 왜 그 오류가 났는지(어떤 값이 비었는지, 무엇이 빠졌는지)는 말하지 않는다. "
             "문법 오류면 그 줄에서 무엇이 빠졌거나 어긋났는지 묻고, 실행 중 오류면 그 줄에 왔을 때 관련 변수에 무엇이 들어 있는지 묻는다. 고친 줄은 쓰지 않는다.",
    "form": "같은 문법을 이 문제와 상관없는 예(과일 이름, 점수 등)로 짧게 한 줄 보여 주고, 사용자의 그 줄과 무엇이 다른지 묻는다. 사용자의 줄을 고쳐 쓰지 않는다.",
}


# 첫 질문을 진단과 한 번에 받는다(모델 호출을 늘리지 않는다). 늘 같던 정해진 글('코드 첫 줄부터 손으로 따라가 보면…')은 실패 입력과 코드의 단서를 쓰지 않았다
OPENING_RULE = ("opening: 사용자에게 보일 첫 질문 한 문장. 실패한 입력과 사용자 코드에서 바로 보이는 단서 하나(입력의 어떤 값·순서·크기, 코드에서 그 값을 다루는 부분)를 짚어 "
                "그것을 살펴보게 묻는다. 원인, 줄 번호, 고친 줄, 고치는 법은 말하지 않는다. 기대한 값·실제 값은 앞에 따로 붙으니 되풀이하지 않는다. "
                "쉬운 한국어로 상대에게 직접 하는 말이고, 물음표로 끝난다.")


def _head(state: MainState, guide: bool = False) -> list[str]:
    """캐시되는 앞부분: 문제, 언어. 진단(locate)만 풀이 가이드와 정답 코드를 본다.

    질문과 원인 판정에는 가이드를 넣지 않는다: 디버깅은 사용자 코드의 방향을 따르는 일인데, 재 보니
    가이드를 본 튜터가 사용자가 말하지 않은 정석 풀이(예: 쌓아 두었다가 짝짓기)를 먼저 꺼냈다.
    """
    ctx = state["ctx"]
    return [f"문제:\n{ctx.problem_text}", f"언어:{ctx.language}", *(solution_lines(state, code=True) if guide else [])]


def _result_lines(state: MainState) -> list[str]:
    report = state["request"].report or {}
    lines = [f"사용자 코드(줄 번호 붙임):\n{numbered(state['request'].code or '')}", f"채점 결과:{FAIL_WORD.get(report.get('status'), report.get('status'))}", f"증상:{symptom(report)}"]
    tail = error_tail(report)
    if tail:
        lines.append(f"오류 메시지:\n{tail}")
    failed = [c for c in report.get("cases") or [] if c.get("status") != "passed"][:3]
    rule = size_rule(state["ctx"].size)
    if rule and (report.get("status") == "timeout" or any(c.get("status") == "timeout" for c in failed)):
        lines.append(f"참고 — 입력 크기 경험칙(시간 초과의 원인이 반복 횟수일 때만 쓴다): {rule}")
    for case in failed:
        lines.append(f"- 입력 {case.get('input')} → 기대 {case.get('expected')}, 실제 {str(case.get('got') or '').strip()[:200]}")
    return lines


def locate_messages(state: MainState) -> list[dict]:
    head = _head(state, guide=True)
    lines = head + _result_lines(state) + [
        "지금 실패를 일으키는 첫 원인 하나만 찾는다(여러 군데가 틀렸어도 하나).",
        "kind: syntax(문법·들여쓰기 오류), runtime(실행 중 오류), logic(끝까지 돌지만 답이 틀림) 중 하나.",
        "line: 원인이 있는 줄 번호(위 코드에 붙인 번호). cause: 무엇이 왜 틀렸는지 한두 문장. fixed_line: 그 줄을 고친 한 줄(줄 번호 없이, 들여쓰기 공백 포함).",
        "사용자의 풀이 방향은 그대로 두고, 가장 적게 고치는 쪽으로 본다.",
        OPENING_RULE,
        'JSON {"kind", "line", "cause", "fixed_line", "opening"}',
    ]
    return [{"role": "system", "content": LOCATE_SYSTEM}, cached_user(lines, len(head))]


def found_messages(state: MainState) -> list[dict]:
    draft = state["draft"]
    head = _head(state)
    lines = head + [
        f"사용자 코드(줄 번호 붙임):\n{numbered(state['request'].code or '')}",
        f"진단(사용자에게 보이지 않음): {draft['line']}번째 줄. {draft['cause']}",
        f"튜터의 직전 질문:{draft['last_question']}",
        "판단 기준: 사용자가 틀린 곳(그 줄이나 그 줄이 하는 일)과 왜 틀렸는지를 자기 말로 짚었으면 Y다. 고치는 법까지 말하지 않아도 된다. "
        "증상만 되풀이하거나 다른 곳을 짚거나 모르겠다고 하면 N이다.",
        f"사용자 말:{state['request'].text or ''}",
    ]
    # 같은 코드의 디버그 턴마다 코드와 진단까지는 같다. 캐시 경계를 그 뒤(직전 질문 앞)에 둔다
    return [{"role": "system", "content": "너는 코딩테스트 튜터의 판정자다. 판정만 하고 설명하지 않는다."}, cached_user(lines, len(head) + 2)]


def speak_messages(state: MainState) -> list[dict]:
    draft = state["draft"]
    head = _head(state)
    stable = head + _result_lines(state) + [
        f"진단(사용자에게 보이지 않음): {draft['line']}번째 줄. {draft['cause']}",
        f"고친 줄(절대 말하지 않는다): {draft['fixed_line']}",
        "디버깅 대화:",
    ]
    lines = stable + (draft["recent"] or ["없음"])
    examples = skill_examples(state["ctx"].skills)
    if examples and draft["step_name"] in ("form", "fix", "cause"):
        lines += ["참고 — 문법 예(이 문제와 상관없는 변수로 쓴 것. 같은 문법을 보여 줄 때만 쓴다):", *examples]
    aside = draft.get("aside")
    if aside:  # 그 말에는 답하지 않는다. 거절과 대안은 엔진이 앞에 붙인다(rules.ANSWER_LEAD)
        lines.append(f"사용자가 방금 {'고친 코드나 답을 달라고 했다' if aside == 'A' else '문제와 무관한 말을 했다'}. 안내 문장은 앞에 따로 붙는다. "
                     "그 말에 대해서는 아무 말도 하지 않고, 이번 질문 지시대로 질문만 쓴다.")
    elif state["request"].text:
        lines.append(f"사용자 말:{state['request'].text}")
        lines += many_asks_line(state["request"].text)
    lines += [f"이번 질문 지시: {STEP_TEXT[draft['step_name']]}", "출력: 말풍선 글만. 따옴표, 머리말, JSON 없이."]
    # 같은 코드의 디버그 턴마다 코드·채점·진단까지는 같다(바뀌는 것은 대화부터). 캐시 경계를 그 뒤에 둔다
    return [{"role": "system", "content": SPEAK_SYSTEM}, cached_user(lines, len(stable))]
