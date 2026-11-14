"""A5 해설. write --> check_sections."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..state import MainState
from . import nodes

STEPS = {"N1": "write", "N2": "check_sections"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("write", nodes.write)
    g.add_node("check_sections", nodes.check_sections)
    g.add_edge(START, "write")
    g.add_edge("write", "check_sections")
    g.add_edge("check_sections", END)
    return g.compile()
