"""A4 블록 설계와 A10 피드백이 같이 쓰는 채점과 전략."""

from ..state import MainState, fail
from .scope import QUALITY_THRESHOLD, SOLVE_SCOPE
from .verdict import SCORE_RULE, ask_verdict

RUBRIC = "\n".join(
    [
        "- 0–29: 방향이 없다. 유형을 못 잡았거나 코드가 문제와 무관하다.",
        "- 30–49: 유형은 맞지만 핵심 자료구조나 흐름이 빠졌다.",
        "- 50–79: 방향이 맞다. 블록 일부가 빠지거나 경계 처리가 틀렸다.",
        "- 80–100: 거의 완성. 작은 실수만 있다.",
    ]
)


def has_code(code: str | None) -> bool:
    return bool((code or "").strip())


def valid_score(score) -> bool:
    return isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 100


def pick_strategy(code_present: bool, score: int | None, direction_ok: bool | None) -> str:
    if not code_present:
        return "fresh"
    if score is None or direction_ok is None or score < QUALITY_THRESHOLD or not direction_ok:
        return "canonical"
    return "keep_flow"


def assess_messages(state: MainState, code: str) -> list[dict]:
    ctx = state["ctx"]
    return [
        {
            "role": "user",
            "content": (
                f"문제:\n{ctx.problem_text}\n언어:{ctx.language}\n풀이 유형:\n{SOLVE_SCOPE}\n"
                f"채점 기준표:\n{RUBRIC}\n방향이 맞다는 것은 문제에 맞는 유형으로 풀고 있다는 뜻이다.\n\n코드:\n{code}"
            ),
        }
    ]


def route_by_code(code_of):
    def route(state: MainState) -> str:
        return "assess" if has_code(code_of(state)) else "pick_strategy"

    return route


def assess_node(task: str, code_of):
    def assess(state: MainState) -> dict:
        got = ask_verdict(assess_messages(state, code_of(state)), SCORE_RULE, task)
        if got is None or not valid_score(got.score):
            return fail("invalid_output", "점수는 0에서 100입니다.")
        return {"score": got.score, "direction_ok": got.ok}

    return assess


def pick_strategy_node(code_of):
    def pick_strategy_step(state: MainState) -> dict:
        if state.get("follow"):
            return {"strategy": "follow", "score": None, "direction_ok": None}
        if not has_code(code_of(state)):
            # 같은 요청에서 A4 다음 A10이 돌 수 있다. 앞 점수를 지운다.
            return {"strategy": "fresh", "score": None, "direction_ok": None}
        return {"strategy": pick_strategy(True, state.get("score"), state.get("direction_ok"))}

    return pick_strategy_step
