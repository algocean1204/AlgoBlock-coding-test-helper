"""A9 블록 채우기. gather --> write_block."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..state import MainState
from . import nodes

STEPS = {"N1": "gather", "N2": "write_block"}


@cache
def graph():
    g = StateGraph(MainState)
    g.add_node("gather", nodes.gather)
    g.add_node("write_block", nodes.write_block)
    g.add_edge(START, "gather")
    g.add_edge("gather", "write_block")
    g.add_edge("write_block", END)
    return g.compile()
