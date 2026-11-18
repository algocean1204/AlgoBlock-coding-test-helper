"""A5 노드. N1 write, N2 check_sections."""

import logging
import re

from ..common.solution import solution_of
from ..common.talk_rules import shape_problems, tidy
from ..llm import llm, model_name
from ..state import Explain, MainState
from .prompts import write_messages
from .rules import check_sections as check_rule

LOG = logging.getLogger("graph.shape")  # 긴 글의 꼴을 어긴 곳(평가기가 모은다. 다시 부르지 않는다)


def write(state: MainState) -> dict:
    return {"draft": llm(model_name()).use(write_messages(state), Explain, task="explain.write")}


def check_sections(state: MainState) -> dict:
    error = check_rule(state["draft"])
    if error:
        return {"error": error, "draft": None}
    for section in state["draft"].sections:
        section.body = tidy(section.body)
        found = shape_problems(section.body)
        if found:
            LOG.info("긴 글 꼴", extra={"where": f"explain.{section.title}", "problems": found})
    guide = solution_of(state)
    if guide is not None:  # 해설의 전체 코드는 풀이 가이드의 코드 그대로다(블록을 이은 것과 같다). 모델이 옮기다 바꾼 것을 되돌린다
        last = state["draft"].sections[-1]
        fence = f"```{state['ctx'].language}\n{guide.code}\n```"
        found = list(re.finditer(r"```[a-zA-Z0-9]*\n.*?```", last.body, re.DOTALL))
        last.body = last.body[: found[-1].start()] + fence + last.body[found[-1].end():] if found else f"{last.body.rstrip()}\n\n{fence}"
    return {"result": {"explain": state["draft"]}, "draft": None}
