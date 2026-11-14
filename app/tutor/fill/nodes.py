"""A9 노드. N1 gather, N2 write_block. 블록이 계획에 있고 열렸는지는 A3이 한 번만 본다. 펜스는 A11이 벗긴다.

채우기는 계획의 그 블록 코드(reference)를 글자 그대로(앞 공백 포함) 돌려준다. 모델이 다시 쓰면 들여쓰기가 사라지고
계획에 없는 변수가 생겼다. reference가 빈 옛 계획만 모델이 쓴다.
내 이름('conveyor')으로 통과한 뒤 채운 블록에 계획 이름('belt')이 들어와 손으로 바꿔야 했다. 그 블록 자리의 이름 바꾸기 표(앞 블록들의 짝)를 적용해 돌려준다.
"""

import re

from ..common.progress_view import active_plan
from ..common.solution import _LEX, frame_of, solution_of, spliced, swap_names
from ..common.talk_rules import EXAMPLES_ONLY, UNRUN_FIX, unrun_why
from ..llm import llm, model_name
from ..state import BlockCode, BlockState, MainState, fail
from ..turn.code_check import USER_FAULT, _analysis, code_hash, guide_gap, kept_code, passed_pairs, program_of, saved_states, tables_of
from .prompts import earlier_code, write_messages


def _block(state: MainState):
    plan = active_plan(state)
    return plan, next(item for item in plan.blocks if item.id == state["request"].block_id)


def gather(state: MainState) -> dict:
    plan, block = _block(state)
    return {"draft": earlier_code(state, plan, block)}


FILL_NOTE = "앞 블록의 내 이름에 맞춰 채우지 못해 튜터의 이름으로 채웠어요. 모으기 전에 이름({names})을 맞춰 주세요."
FILL_GUESS = "채운 코드는 내 이름({mine})을 {each}튜터의 이름({plan})의 뜻으로 짐작해 썼어요. 뜻이 다르면 이 칸에서 고쳐 주세요."
FILL_UNRUN = "채운 코드는 실행하지 못해서({why}) 확인 전이에요."
FILL_REFUSED = "튜터의 풀이를 확인하지 못해 이 블록을 채울 수 없어요. 직접 적어 주세요."  # 확인하지 못한 풀이의 코드는 없는 이름이나 빈 자리를 품을 수 있어 넣지 않는다
FILL_FAIL = "채운 코드를 다른 블록의 내 코드와 이어 돌리면 아직 통과하지 않아요. 모으기 전에 '블록 코드 확인'으로 앞뒤 블록을 다시 확인해 주세요."


def tidy(code: str, language: str, indent: int) -> str:
    """채울 글에서 튜터 풀이의 설명 주석을 빼고, 첫 알맹이 줄의 들여쓰기(indent)만큼 왼쪽으로 당긴다(블록 칸은 그 줄을 맨 앞에 두고 쓴다. 놓는 것은 이어 붙일 때 한다)."""
    plain = _LEX[language].sub(lambda m: "" if m.lastgroup == "c" else m.group(0), code) if language in _LEX else code
    rows = code.splitlines() if len(plain.splitlines()) != len(code.splitlines()) else [new.rstrip() for old, new in zip(code.splitlines(), plain.splitlines()) if new.strip() or not old.strip()]
    return "\n".join(row[min(indent, len(row) - len(row.lstrip())):] for row in rows)


def write_block(state: MainState, config=None) -> dict:
    """표로 이름을 바꾼 채울 글을 넣어 이어 돌려 본다(채점 함수가 있으면). 통과하면 그 글로 채우고, 통과하지 못하면 계획의 이름 그대로 채우고 알린다.
    채운 글은 그대로 저장한다(뒤 블록 확인의 이어 붙이기가 화면의 글과 같아야 한다). 실행으로 확인하지 못한 채운 글(채점하지 못함, 풀이 가이드를
    믿을 수 없음)은 '확인 전'(?)으로 남기고 그렇게 말한다. 판정 규칙은 블록 코드 확인(turn/code_check)과 같다."""
    plan, block = _block(state)
    if block.reference.strip():
        guide = solution_of(state)
        if guide is None or guide.verified is False:
            return fail("fill_unavailable", FILL_REFUSED)
        index = plan.blocks.index(block)
        base = tables_of(state, plan, passed_pairs(state, plan, skip=index))
        table = base[index]
        language = state["ctx"].language
        frame, rows = frame_of(block.reference, language, program_of(state)), block.reference.splitlines()
        # 블록 칸에는 알맹이만 놓는다: 머리·꼬리(진입 함수 머리, 닫는 괄호)는 이어 붙일 때 틀이 넣는다. 바깥으로 나가는 줄이 있으면 들여쓰기의 차를 지키려 그대로 둔다
        body, indent = "\n".join(rows[len(frame["head"]):len(rows) - len(frame["tail"])]) or block.reference, 0 if frame["outer"] else frame["indent"]
        code, note, verdict = tidy(swap_names(body, table, language), language, indent), "", "Y"
        words = set(re.findall(r"[A-Za-z_]\w*", block.reference))
        # 앞 블록의 굳지 않은 무리(꼴이 같은 이름들)의 첫 가정으로 바꾼 이름은 짐작이다: 그 가정을 보인다(뒤 블록이 다른 차례를 고르면 이 칸의 글은 그대로다)
        guess = [[table.get(p, p), p] for _, plans, _ in _analysis(state, plan, index, code, base)[1] for p in plans if p in words]
        if guess:
            note = FILL_GUESS.format(mine=", ".join(f"`{m}`" for m, _ in guess), plan=", ".join(f"`{p}`" for _, p in guess), each="차례대로 " if len(guess) > 1 else "")
        check = ((config or {}).get("configurable") or {}).get("check")
        refs, language, states = [b.reference for b in plan.blocks], state["ctx"].language, saved_states(state)
        mine = {i: states[b.id].code for i, b in enumerate(plan.blocks) if i != index and b.id in states}
        said = ""  # 실행으로 확인하지 못한 까닭의 말(있으면 '확인 전')
        gap = guide_gap(state, check) if len(mine) + 1 < len(refs) else None  # 계획 코드로 잇는 블록(이 블록·내 블록 말고)이 있는데 풀이 가이드를 믿을 수 없다: 그 결과는 판정이 아니다
        if gap is not None:
            said = FILL_UNRUN.format(why=unrun_why(gap.get("unrun", ""))) + UNRUN_FIX.get(gap.get("unrun", ""), "")
        elif check is None:
            said = FILL_UNRUN.format(why=unrun_why(""))
        else:
            tables = tables_of(state, plan, passed_pairs(state, plan))
            report = check(state["ctx"].problem_id, spliced(refs, index, code, language, mine, tables, program_of(state), state["ctx"].starter), quick=True) or {}
            status = report.get("status")
            if status in USER_FAULT:
                names = [p for p, m in table.items() if p in words and m != p]
                # 표로 바꾼 글이 통과하지 못했다: 계획의 이름 그대로 채우고 알린다. 바꾼 이름이 없으면 그 글 그대로 두고 통과하지 않는다는 것만 알린다
                code, verdict = tidy(body, language, indent), "?"
                note = FILL_NOTE.format(names=", ".join(f"`{n}`" for n in names)) if names else FILL_FAIL
            elif status != "passed":
                said = FILL_UNRUN.format(why=unrun_why(status or "")) + UNRUN_FIX.get(status or "", "")
            elif (cases := report.get("cases") or []) and all(case.get("kind") == "example" for case in cases):  # 숨은 테스트 없이 공개 예시로만 돌았다
                note = f"{note} {EXAMPLES_ONLY}".strip()
        if said:
            verdict, note = "?", f"{note} {said}".strip()
        # 틀린 수(tries − 통과)는 바꾸지 않는다: 통과하지 못한 상태가 있었으면 tries를 하나 올린다
        saved = saved_states(state).get(block.id)
        tries = (saved.tries + (saved.verdict not in ("Y", "?"))) if saved else 1
        record = BlockState(block.id, kept_code(code), code_hash(code), verdict, None, tries, [])
        return {"result": {"code": code, **({"note": note} if note else {})}, "draft": None, "block_check": record}  # 모델 0회
    written = llm(model_name()).use(write_messages(state, block, state["draft"]), BlockCode, task="fill.write_block")
    return {"result": {"code": written.code}, "draft": None}
