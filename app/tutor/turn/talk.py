"""N5 질문 만들기 프롬프트와 N6 말풍선 검사."""

import logging

from ..common.solution import solution_lines
from ..llm import cached_user
from ..common.progress_view import active_plan
from ..common.scope import algorithm_line
from ..common.talk_prompts import CONCEPT_FIRST, learner_lines
from ..common.talk_rules import FALLBACK, kind_word, note_fallback, repair, reply_problems
from ..knowledge.ontology import hidden_terms
from ..request_check.nodes import mode_messages
from ..state import MainState, MovePlan, TurnContext

LOG = logging.getLogger("graph.talk")  # 대체 질문이 나간 이유(평가기가 모은다)


def speak_messages(state: MainState, turn: TurnContext, move: MovePlan, system: str, steps: dict) -> list[dict]:
    """묻는 블록 하나만. 참고 코드와 그 뒤 블록은 넣지 않는다."""
    plan = active_plan(state)
    block = plan.blocks[move.target]
    ctx = state["ctx"]
    guide = solution_lines(state)
    lines = [f"문제:\n{ctx.problem_text}", f"언어:{ctx.language}", *guide]
    algorithm = algorithm_line(plan.algorithm)
    if algorithm:
        lines.append(algorithm)
    if plan.link:
        lines.append(f"참고 — 사용자가 전에 풀어 본 같은 구조의 문제: {plan.link} (사용자가 막혔을 때 그 문제를 떠올리게 하는 한마디로만 쓴다. 그 풀이를 대신 말하지 않는다)")
    recent = turn.recent if move.target == turn.index else []
    lines += [f"물을 블록:{block.name} ({kind_word(block.kind)})", f"이 블록에서 정할 것:{block.goal}", "이 블록의 최근 대화:", *(recent or ["없음"])]
    aside = getattr(state.get("verdict"), "aside", "")
    if turn.text and not aside:
        lines.append(f"사용자 말:{turn.text}")
    if aside:  # 그 말에는 답하지 않는다. 안내 문장은 엔진이 앞에 붙인다
        lines.append(f"사용자가 방금 {'답을 달라고 했다' if aside == 'A' else '문제와 무관한 말을 했다'}. 안내 문장은 앞에 따로 붙는다. "
                     "이 말이나 앞 대화의 부탁에 대해서는 아무 말도 하지 않고, 지금 블록을 겨눈 질문 한 문장만 쓴다.")
    if turn.event == "block_filled" and move.target == turn.index:  # 코드 확인 턴은 말 턴과 다르다(코드를 질문으로 읽었다)
        lines += [f"사용자가 방금 이 블록의 코드를 확인받았다. 질문을 한 것이 아니다. 적은 코드:\n{state['request'].code or ''}",
                  f"판정: 아직 넘어가지 않는다. 이 코드가 해내지 못한 것: {move.missing_signal}. 다음 질문은 이것 하나만 겨눈다. 다른 것을 묻지 않는다."]
    replying = turn.event == "message" and bool(turn.text) and not aside
    # 가이드는 사용자 말에 답할 때 그 말을 겨눈다(reply). 의자는 유형 지시 뒤에 개념·까닭을 물으면 먼저 답하라는 지시를 붙인다
    step = steps.get("reply", f"{steps[move.move]} {CONCEPT_FIRST}") if replying and move.move != "verify" else steps[move.move]  # verify: 맞는지 물은 말에만 쓰는 지시
    hidden = masked_terms(state)
    if hidden:
        lines.append(f"참고: 사용자가 먼저 말하기 전에는 되도록 쓰지 않을 낱말: {', '.join(hidden)}")
    if move.missing_signal:
        step += f" 가리킬 방향: {move.missing_signal}(그대로 말하지 않는다)."
    lines += learner_lines(ctx)  # 캐시 경계(head) 뒤라 앞부분 캐시는 그대로다
    lines += [f"질문 유형 지시: {step}", "출력: 말풍선 글만. 따옴표, 머리말, JSON 없이."]
    return [{"role": "system", "content": system}, cached_user(lines, 2 + len(guide))]


def clean_text(text: str) -> str:
    body = (text or "").strip()
    if len(body) >= 2 and body[0] == body[-1] and body[0] in "\"'“”":
        body = body[1:-1].strip()
    return body


def masked_terms(state: MainState) -> list[str]:
    """의자가 먼저 꺼내지 않을 기법 낱말(프롬프트 안내용. 온톨로지는 참고 지식이라 말풍선을 막는 규칙으로는 쓰지 않는다).

    문제 글이나 지금까지의 대화에 나온 낱말은 뺀다. 가이드는 기법을 짚어 주는 모드라 없다.
    """
    if state["request"].mode != "chair":
        return []
    known = "\n".join([state["ctx"].problem_text, state["request"].text or "", *(m.text for m in mode_messages(state))])
    return hidden_terms(state["ctx"].patterns, known)


def turn_text(state: MainState) -> str:
    return (state["request"].text or "") if state.get("turn") is None else state["turn"].text


def recent_lines(state: MainState) -> list[str]:
    return [] if state.get("turn") is None else list(state["turn"].recent)


def checked_reply(state: MainState, move: MovePlan, text: str) -> tuple[str, list[str]]:
    """원칙을 어기면 유형별 대체 질문. (말, 위반 이유). 고칠 수 있는 위반(3문장 초과, 되받기, 블록의 답을 말한 평서문 등)은 고쳐서 다시 본다."""
    plan, ctx = active_plan(state), state["ctx"]
    reference = plan.blocks[move.target].reference
    said = "\n".join([turn_text(state), *recent_lines(state)])
    turn = state.get("turn")
    # 가이드가 사용자 말에 답하는 턴은 뒤 블록 이름을 좁혀 본다. 걸리지 않으면 '3문장 초과'는 대체 질문 대신 repair가 뒤 세 문장으로 자른다
    replying = (state["request"].mode == "guide" and turn is not None and turn.event == "message" and bool(turn.text)
                and not getattr(state.get("verdict"), "aside", ""))
    check = dict(move=move.move, problem=ctx.problem_text, reference=reference, later_names=[b.name for b in plan.blocks[move.target + 1 :]],
                 said=said, language=ctx.language, loose_names=replying)
    problems = reply_problems(text, **check)
    if not problems or not {"코드 펜스", "참고 코드", "뒤 블록 이름", "금지 표현", "동의로 시작", "3인칭 메모", "영어 지시문"} & set(problems):
        text = repair(text, ctx.problem_text, said, move.move, reference, ctx.language)
        problems = reply_problems(text, **check)
    if problems:
        LOG.info("대체 질문", extra={"move": move.move, "problems": problems})
        note_fallback(f"{state['request'].mode}.{move.move}", problems, text)
    return (FALLBACK[move.move] if problems else text.strip()), problems
