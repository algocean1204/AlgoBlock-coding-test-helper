"""A12 저장과 응답. collect --> save -- 오류 --> END, 아니면 respond."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..common.errors import stop_on_error
from ..state import MainState
from .nodes import collect, respond, save

STEPS = {"N1": "collect", "N2": "save", "N3": "respond"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("collect", collect)
    g.add_node("save", save)
    g.add_node("respond", respond)
    g.add_edge(START, "collect")
    g.add_edge("collect", "save")
    g.add_conditional_edges("save", stop_on_error("respond"), {"respond": "respond", "end": END})
    g.add_edge("respond", END)
    return g.compile()
