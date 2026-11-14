"""A5 노드. N1 write, N2 check_sections."""

import re

from ..common.solution import solution_of
from ..llm import llm, model_name
from ..state import Explain, MainState
from .prompts import write_messages
from .rules import check_sections as check_rule


def write(state: MainState) -> dict:
    return {"draft": llm(model_name()).use(write_messages(state), Explain, task="explain.write")}


def check_sections(state: MainState) -> dict:
    error = check_rule(state["draft"])
    if error:
        return {"error": error, "draft": None}
    guide = solution_of(state)
    if guide is not None:  # 해설의 전체 코드는 풀이 가이드의 코드 그대로다(블록을 이은 것과 같다). 모델이 옮기다 바꾼 것을 되돌린다
        last = state["draft"].sections[-1]
        fence = f"```{state['ctx'].language}\n{guide.code}\n```"
        found = list(re.finditer(r"```[a-zA-Z0-9]*\n.*?```", last.body, re.DOTALL))
        last.body = last.body[: found[-1].start()] + fence + last.body[found[-1].end():] if found else f"{last.body.rstrip()}\n\n{fence}"
    return {"result": {"explain": state["draft"]}, "draft": None}
