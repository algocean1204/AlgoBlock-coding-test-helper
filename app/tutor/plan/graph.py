"""A4 블록 설계.

abstract(뼈대 뽑기) --> 코드 있음: assess --> pick_strategy / 코드 없음: pick_strategy
pick_strategy --> solve(풀이 가이드: 문제 글만 보고 풀고 채점기로 확인) --> recall(참고와 지난 문항 한 줄)
--> draft_blocks(가이드 코드를 순서대로 나눔) --> check_blocks --> clean_hints
오류면 END(계획을 만들지 않는다). 사용자 방법으로 못 풀면 solve에서 END(지금 계획을 지킨다).
"""

from functools import cache

from langgraph.graph import END, START, StateGraph

from ..common.assess import route_by_code
from ..common.errors import stop_on_error
from ..state import MainState
from . import nodes

STEPS = {"N1": "abstract", "N2": "assess", "N3": "pick_strategy", "N4": "solve", "N5": "recall", "N6": "draft_blocks", "N7": "check_blocks", "N8": "clean_hints"}


@cache
def graph():
    g = StateGraph(MainState)
    for name in STEPS.values():
        g.add_node(name, getattr(nodes, name))
    by_code = route_by_code(nodes.direct_code)
    # 사용자가 말한 방법으로 다시 짤 때는 코드 채점을 건너뛴다
    g.add_edge(START, "abstract")
    g.add_conditional_edges("abstract", lambda s: "pick_strategy" if s.get("follow") else by_code(s), {"assess": "assess", "pick_strategy": "pick_strategy"})
    g.add_conditional_edges("assess", stop_on_error("pick_strategy"), {"pick_strategy": "pick_strategy", "end": END})
    g.add_edge("pick_strategy", "solve")
    g.add_conditional_edges("solve", lambda s: "end" if s.get("replanned") == "rejected" else "recall", {"recall": "recall", "end": END})
    g.add_edge("recall", "draft_blocks")
    g.add_conditional_edges("draft_blocks", stop_on_error("check_blocks"), {"check_blocks": "check_blocks", "end": END})
    g.add_conditional_edges("check_blocks", stop_on_error("clean_hints"), {"clean_hints": "clean_hints", "end": END})
    g.add_edge("clean_hints", END)
    return g.compile()
