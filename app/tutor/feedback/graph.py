"""A10 피드백.

제출 코드 있음 --> assess --> pick_strategy --> analyze --> check_feedback
제출 코드 없음 --> pick_strategy --> …
"""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..common.assess import route_by_code
from ..common.errors import stop_on_error
from ..state import MainState
from . import nodes

STEPS = {"N1": "assess", "N2": "pick_strategy", "N3": "analyze", "N4": "check_feedback"}


@cache
def graph():
    g = StateGraph(MainState)
    for name in STEPS.values():
        g.add_node(name, getattr(nodes, name))
    g.add_conditional_edges(START, route_by_code(nodes.submitted_code), {"assess": "assess", "pick_strategy": "pick_strategy"})
    g.add_conditional_edges("assess", stop_on_error("pick_strategy"), {"pick_strategy": "pick_strategy", "end": END})
    g.add_edge("pick_strategy", "analyze")
    g.add_edge("analyze", "check_feedback")
    g.add_edge("check_feedback", END)
    return g.compile()
