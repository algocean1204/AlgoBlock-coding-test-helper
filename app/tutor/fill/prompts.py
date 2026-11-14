"""이 블록의 참고 코드와 앞 블록만. 뒤 블록은 넣지 않는다."""

from ..common.solution import solution_lines
from ..llm import cached_user
from ..common.scope import system_prompt
from ..turn.code_check import saved_states
from ..state import MainState


def earlier_code(state: MainState, plan, block) -> list[str]:
    """N1 앞 블록 모으기. 저장된 블록 코드에 요청으로 온 코드를 덮어쓴다."""
    index = plan.blocks.index(block)
    filled = {key: item.code for key, item in saved_states(state).items()}
    filled |= {item.id: item.code for item in state["request"].filled}
    return [f"- {prev.name}: {filled.get(prev.id) or '비어 있음'}" for prev in plan.blocks[:index]] or ["없음"]


def write_messages(state: MainState, block, earlier: list[str]) -> list[dict]:
    language = state["ctx"].language
    system = system_prompt(
        "너는 코딩테스트 튜터다. 사용자가 막힌 블록 하나의 코드만 써 준다.",
        "규칙:",
        "- 이 블록의 코드만 쓴다. 앞 블록 코드를 다시 쓰지 않는다. 뒤 블록을 미리 쓰지 않는다.",
        "- 앞 블록에 나온 변수 이름을 그대로 쓴다.",
        f"- {language}의 기본 문법과 표준 라이브러리만 쓴다. 주석은 쓰지 않는다.",
        "- 들여쓰기는 이 블록이 놓일 자리 기준이다.",
    )
    guide = solution_lines(state)
    lines = [f"문제:\n{state['ctx'].problem_text}", f"언어:{language}", *guide, "앞 블록:", *earlier]
    lines += [
        f"이 블록:{block.name} ({block.kind})",
        f"이 블록에서 정할 것:{block.goal}",
        f"참고 코드:\n{block.reference}",
        '출력: JSON {"code": "이 블록 코드만"}',
    ]
    return [{"role": "system", "content": system}, cached_user(lines, 2 + len(guide))]
