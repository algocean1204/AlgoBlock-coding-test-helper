"""A2 그래프. load_context(N1) -- 오류 --> END, 아니면 cached_response(N2) --> END."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..common.errors import stop_on_error
from ..state import MainState
from .nodes import cached_response, load_context

STEPS = {"N1": "load_context", "N2": "cached_response"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("load_context", load_context)
    g.add_node("cached_response", cached_response)
    g.add_edge(START, "load_context")
    g.add_conditional_edges("load_context", stop_on_error("cached_response"), {"cached_response": "cached_response", "end": END})
    g.add_edge("cached_response", END)
    return g.compile()
