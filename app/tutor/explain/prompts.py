from ..common.progress_view import active_plan
from ..common.solution import solution_lines
from ..common.scope import algorithm_line, system_prompt
from ..common.talk_rules import kind_word
from ..state import EXPLAIN_TITLES, MainState

SECTION_TEXT = (
    "입력, 출력, 제약에서 풀이를 정하는 단서",
    "풀이 유형 이름으로 시작해, 왜 이 유형인지와 큰 흐름 세 줄 이내",
    "블록마다 한 줄. 이 블록이 왜 이 자리에 오는지",
    "블록 순서대로 설명한다",
)
WHOLE_CODE = ", 끝에 블록을 이은 전체 코드를 코드 블록 하나로 둔다"  # 가이드가 없을 때만. 있으면 가이드 코드를 그대로 붙인다(nodes.check_sections). 모델이 옮겨 쓰는 출력을 아낀다


def write_messages(state: MainState) -> list[dict]:
    plan = active_plan(state)
    system = system_prompt("너는 코딩테스트 튜터의 해설자다. 위에서 아래로 읽는 글을 쓴다.")
    guide = solution_lines(state, code=True)
    lines = [f"문제:\n{state['ctx'].problem_text}", f"언어:{state['ctx'].language}", *guide]
    algorithm = algorithm_line(plan.algorithm) if plan else None
    if algorithm:
        lines.append(algorithm)
    if plan:
        lines.append("블록(흐름 순서):")
        for number, block in enumerate(plan.blocks, 1):
            lines += [f"{number}. {block.name} ({kind_word(block.kind)}) — {block.goal}", f"   참고: {block.reference}"]
    if guide:
        lines.append("첫 절은 풀이 가이드의 단서를 바탕으로 쓴다. 전체 코드는 쓰지 않는다(위 정답 코드가 마지막 절 끝에 그대로 붙는다).")
    lines.append("네 절을 이 제목과 순서로만 쓴다.")
    lines += [f"- {title}: {text}" for title, text in zip(EXPLAIN_TITLES, SECTION_TEXT[:-1] + (SECTION_TEXT[-1] + ("" if guide else WHOLE_CODE),))]
    lines.append('출력: JSON {"sections": [{"title", "body"}] 네 개}')
    # 캐시 표시를 하지 않는다: 문제×언어마다 한 번 부르는(만든 해설은 저장한다) 호출이라 앞부분이 다시 읽히지 않고, 표시하면 쓰기 할증(1.25배)만 붙는다
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}]
