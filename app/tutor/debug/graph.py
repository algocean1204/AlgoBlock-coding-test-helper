"""A13 디버그: 사용자가 쓴 코드의 틀린 곳을 스스로 찾게 묻는다.

gather(N1) -- 새 코드 --> locate(N2) --> pick_step(N4)
gather -- 같은 코드 + 사용자 말 --> judge(N3) --> pick_step
gather -- 같은 코드, 말 없음 --> pick_step
pick_step --> speak(N5) --> check_reply(N6) --> END
"""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..state import MainState
from . import nodes

STEPS = {"N1": "gather", "N2": "locate", "N3": "judge", "N4": "pick_step", "N5": "speak", "N6": "check_reply"}


def after_gather(state: MainState) -> str:
    draft = state["draft"]
    if not draft["cached"]:
        return "locate"
    return "judge" if (state["request"].text or "").strip() else "pick_step"


@cache
def graph():
    g = StateGraph(MainState)
    for name in STEPS.values():
        g.add_node(name, getattr(nodes, name))
    g.add_edge(START, "gather")
    g.add_conditional_edges("gather", after_gather, {"locate": "locate", "judge": "judge", "pick_step": "pick_step"})
    g.add_edge("locate", "pick_step")
    g.add_edge("judge", "pick_step")
    g.add_edge("pick_step", "speak")
    g.add_edge("speak", "check_reply")
    g.add_edge("check_reply", END)
    return g.compile()
