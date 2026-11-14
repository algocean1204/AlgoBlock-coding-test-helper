"""A7 가이드. 그래프는 turn/graph.py를 의자와 같이 쓴다(블록을 여는 말과 내용 없는 답 뒤는 저장 힌트)."""

from functools import cache

from ..common.verdict import FOUND_RULE
from ..turn.graph import STEPS, turn_graph  # noqa: F401  (STEPS: 단계 이름, 의자·가이드 공통)
from .prompts import MOVE_TEXT, SYSTEM, judge_messages


@cache
def graph():
    return turn_graph("guide", judge_messages, FOUND_RULE, SYSTEM, MOVE_TEXT)
