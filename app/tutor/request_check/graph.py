"""A3 그래프. check_request(N1) 한 단계."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..state import MainState
from .nodes import check_request

STEPS = {"N1": "check_request"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("check_request", check_request)
    g.add_edge(START, "check_request")
    g.add_edge("check_request", END)
    return g.compile()
