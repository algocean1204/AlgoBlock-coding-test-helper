"""의자·가이드·꼬리질문 시스템 프롬프트. 대화 원칙은 talk_rules.py 머리말과 같다."""

from ..knowledge.ontology import PITFALLS
from ..llm import cached_user
from .solution import solution_lines
from .scope import PRINCIPLES
from .talk_rules import BANNED

_BANNED = ", ".join(BANNED)

LEVEL_TEXT = {
    "beginner": "학습자는 입문 단계다. 용어를 쓰면 한 구절로 풀어 말하고, 한 번에 한 가지만 묻는다.",
    "advanced": "학습자는 익숙한 단계다. 기본 설명을 줄이고, 경계 입력과 시간 복잡도를 겨누는 질문을 먼저 고른다.",
}


def weak_pitfalls(ctx) -> list[str]:
    """이 사용자가 여러 문항에서 되풀이한 함정 '이름(n번)', 많아야 3개. 계획·피드백·의자·가이드가 같이 쓴다."""
    return [f"{PITFALLS[pid][1]}({count}번)" for pid, count in ctx.frequent_pitfalls if pid in PITFALLS][:3]


def learner_lines(ctx) -> list[str]:
    """의자·가이드 질문 프롬프트의 '학습자' 구역. 눈높이가 middle이고 함정도 없으면 비운다(프롬프트가 예전과 같다)."""
    lines = []
    weak = weak_pitfalls(ctx)
    if weak:
        lines.append(f"이 학습자가 다른 문제에서 되풀이한 실수: {', '.join(weak)}. "
                     "지금 블록이 이 실수와 닿을 때만, 그 지점을 스스로 확인하게 하는 질문을 고른다. 실수의 이름을 그대로 말하지 않는다.")
    if ctx.level in LEVEL_TEXT:
        lines.append(LEVEL_TEXT[ctx.level])
    return ["학습자:", *lines] if lines else []


def talk_system(role: str, basis: bool) -> str:
    second = (
        "2. 네가 단서를 줄 때는 문제 글 문장을 작은따옴표로 그대로 인용하고, 문제 글에 없는 것을 사실처럼 말하지 않는다. "
        "사용자의 생각이 문제 글에서 나왔는지 짐작인지는 '근거' 질문 지시가 있을 때만 묻는다. 그 밖의 질문에는 붙이지 않는다."
        if basis
        else "2. 단서를 줄 때는 문제 글 문장을 작은따옴표로 그대로 인용하고, 문제 글에 없는 것을 사실처럼 말하지 않는다. "
        "사용자에게 주장의 근거를 묻는 질문은 하지 않는다."
    )
    return "\n".join(
        [
            role,
            "원칙:",
            PRINCIPLES,
            "대화 원칙:",
            "1. 판정을 먼저 말하지 않는다. 첫 문장은 사용자의 말 속 가정, 빠진 경우, 근거를 겨누는 질문이다.",
            "사용자의 말을 되풀이하거나 요약하는 문장으로 시작하지 않는다. 첫 문장부터 가정·빠진 경우·근거를 겨눈다.",
            second,
            f"3. 생각을 닫는 말을 쓰지 않는다: {_BANNED}.",
            "금지: 참고 코드, 다음 블록의 이름, 답 코드, 코드 블록.",
            "사용자가 직접 물은 것이 있으면 그 물음부터 받는다: 그 물음을 스스로 풀 실마리를 묻는다. 물음을 못 본 척 다른 질문으로 넘어가지 않는다.",
            "말은 한국어 1~3문장이고 물음표로 끝나는 질문 하나로 끝낸다. 한 번에 한 가지만 묻는다. '그리고'·'아니면'으로 질문을 잇지 않는다.",
            "상대에게 직접 하는 말만 쓴다. '사용자' 같은 3인칭, 네 계획이나 메모, 영어 문장을 쓰지 않는다.",
        ]
    )


# 사용자 말에 답할 때의 지시 끝에 붙인다(가이드 MOVE_TEXT["reply"], 의자는 turn/talk.py). '왜 덱을 써야 하나요?'를 '다만 지금은…'으로 돌렸다
CONCEPT_FIRST = ("사용자가 개념이나 까닭을 물으면 먼저 한두 문장으로 답한다(이 블록이 정하는 값·조건·코드는 말하지 않는다). "
                 "'다만', '하지만', '그런데'로 시작하지 않는다. 그다음 지금 블록을 겨눈 질문 하나를 한다.")

JUDGE_SYSTEM = "너는 코딩테스트 튜터의 판정자다. 판정만 하고 설명하지 않는다."


def judge_lines(state, turn, criteria: str) -> list[dict]:
    """판정 프롬프트 공통. 넣지 않는 것: 언어, 깊이, 참고 코드, 다음 블록, 대화 원칙."""
    block = turn.block
    checks = [f"{n}. {text}" for n, text in enumerate(block.checks, 1)] or ["없음(목표로 판단)"]
    guide = solution_lines(state)
    lines = [
        f"문제:\n{state['ctx'].problem_text}",
        *guide,
        f"지금 블록:{block.name} ({block.kind})",
        f"목표:{block.goal}",
        "신호:",
        *checks,
        f"직전 질문:{turn.last_question}",
        criteria,
        f"사용자 말:{state['request'].text or ''}",
    ]
    return [{"role": "system", "content": JUDGE_SYSTEM}, cached_user(lines, 1 + len(guide), 1 + len(guide) + 3 + len(checks))]
