"""A6 생각하는 의자. 그래프는 turn/graph.py를 가이드와 같이 쓴다."""

from functools import cache

from ..common.verdict import BASIS_RULE
from ..turn.graph import STEPS, turn_graph  # noqa: F401  (STEPS: 단계 이름, 의자·가이드 공통)
from .prompts import MOVE_TEXT, SYSTEM, judge_messages


@cache
def graph():
    return turn_graph("chair", judge_messages, BASIS_RULE, SYSTEM, MOVE_TEXT)
