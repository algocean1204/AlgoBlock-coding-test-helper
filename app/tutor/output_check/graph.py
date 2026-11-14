"""A11 나가는 글 검사. guard -- 오류 --> END, 아니면 progress."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..common.errors import stop_on_error
from ..state import MainState
from .nodes import guard, progress

STEPS = {"N1": "guard", "N2": "progress"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("guard", guard)
    g.add_node("progress", progress)
    g.add_edge(START, "guard")
    g.add_conditional_edges("guard", stop_on_error("progress"), {"progress": "progress", "end": END})
    g.add_edge("progress", END)
    return g.compile()
