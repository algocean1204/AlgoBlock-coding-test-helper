"""A8 꼬리질문. gather --> answer --> check_reply."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..state import MainState
from . import nodes

STEPS = {"N1": "gather", "N2": "answer", "N3": "check_reply"}


@cache
def graph():
    g = StateGraph(MainState)
    for name in STEPS.values():
        g.add_node(name, getattr(nodes, name))
    g.add_edge(START, "gather")
    g.add_edge("gather", "answer")
    g.add_edge("answer", "check_reply")
    g.add_edge("check_reply", END)
    return g.compile()
