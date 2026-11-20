"""튜터 요청 하나의 그래프(연결 L2–L36). 에이전트는 주입받는다(시험에서 가짜로 바꾼다).

context(A2) -- 오류 · 저장된 결과 --> END
context --> request_check(A3) -- 거절 --> END
request_check -- 계획 없음 --> plan(A4) -- 실패 --> END
request_check · plan --> 기능 하나(A5–A10) -- 실패 --> END
기능 --> output_check(A11) -- 거절 --> END
output_check --> save(A12) --> END
저장소는 config["configurable"]["store"]로 넘긴다. 체크포인터는 쓰지 않는다.
모델 예외는 그래프 밖으로 나가 Tutor가 오류로 바꾼다. 그 경우 A12에 닿지 않으므로 아무것도 저장되지 않는다.
"""

import json
from contextlib import nullcontext
from dataclasses import dataclass, replace
from functools import cache

from langgraph.graph import END, START, StateGraph

from .common.errors import STATUS, llm_error
from .llm import LlmError, use_llm
from .save.respond import session_body
from .state import FilledBlock, MainState, Solution, Solved, TutorRequest
from .store import Store
from .store.codec import plan_from_json

FEATURES = ("explain", "chair", "guide", "fill", "feedback", "debug")
NO_PLAN = ("debug",)  # 계획 없이 도는 기능(사용자 코드만 본다)
AGENTS = ("context", "request_check", "plan", *FEATURES, "output_check", "save")


def pick(state: MainState) -> str:
    """요청 종류로 기능 하나(L10–L15, L17–L20)."""
    req = state["request"]
    if req.kind == "turn":
        return req.mode if req.mode in {"chair", "guide"} else "end"
    return req.kind if req.kind in FEATURES else "end"


def after_context(state: MainState) -> str:
    if state.get("error") or state.get("response"):
        return "end"
    return "request_check"


def after_check(state: MainState) -> str:
    if state.get("error"):
        return "end"
    ctx, kind = state["ctx"], state["request"].kind
    if kind == "prepare":
        return "plan" if ctx.plan is None else "end"  # 이미 계획이 있으면 할 일이 없다
    if kind in NO_PLAN:
        return pick(state)
    return "plan" if ctx.plan is None else pick(state)


def after_plan(state: MainState) -> str:
    if state.get("error"):
        return "end"
    return "save" if state["request"].kind == "prepare" else pick(state)


def after_ok(name: str):
    def route(state: MainState) -> str:
        return "end" if state.get("error") else name

    return route


def after_feature(state: MainState) -> str:
    """기능 다음. 의자가 '사용자 방법으로 다시 짜기'를 청하면 A4를 거쳐 의자로 돌아온다(한 요청에 한 번)."""
    if state.get("error"):
        return "end"
    if (state.get("result") or {}).get("replan") and not state.get("replanned"):
        return "plan"
    return "output_check"


def default_agents() -> dict:
    from .chair.graph import graph as chair
    from .context.graph import graph as context
    from .debug.graph import graph as debug
    from .explain.graph import graph as explain
    from .feedback.graph import graph as feedback
    from .fill.graph import graph as fill
    from .guide.graph import graph as guide
    from .output_check.graph import graph as output_check
    from .plan.graph import graph as plan
    from .request_check.graph import graph as request_check
    from .save.graph import graph as save

    made = dict(context=context, request_check=request_check, plan=plan, explain=explain, chair=chair, guide=guide,
                fill=fill, feedback=feedback, debug=debug, output_check=output_check, save=save)
    return {name: build_one() for name, build_one in made.items()}


def build(agents: dict):
    routes = {name: name for name in FEATURES} | {"end": END}
    g = StateGraph(MainState)
    for name in AGENTS:
        g.add_node(name, agents[name])
    g.add_edge(START, "context")
    g.add_conditional_edges("context", after_context, {"request_check": "request_check", "end": END})
    g.add_conditional_edges("request_check", after_check, routes | {"plan": "plan"})
    g.add_conditional_edges("plan", after_plan, routes | {"save": "save"})
    for name in FEATURES:
        g.add_conditional_edges(name, after_feature, {"output_check": "output_check", "plan": "plan", "end": END})
    g.add_conditional_edges("output_check", after_ok("save"), {"save": "save", "end": END})
    g.add_edge("save", END)
    return g.compile()


@cache
def graph():
    return build(default_agents())


def run(state: MainState, store, compiled=None, index=None, check=None, given=None, cross=None, shape=None) -> MainState:
    """모델 예외는 오류로 바꾼다(그 전에 저장된 것은 없다). index는 비슷한 문항 찾기, check는 정답 코드 채점, given은 정해 둔 정답 코드,
    cross는 정답 풀이를 단순 풀이·생성기와 대조하는 실행기, shape는 문항의 방식과 시작 코드(모두 없어도 된다)."""
    try:
        return (compiled or graph()).invoke(state, {"configurable": {"store": store, "index": index, "check": check, "given": given, "cross": cross,
                                                                     "shape": shape}})
    except LlmError as exc:
        return {**state, "error": llm_error(exc), "result": None, "plan": None, "response": None}


@dataclass
class Outcome:
    status: int
    body: dict


def _error(code: str, message: str) -> Outcome:
    return Outcome(STATUS.get(code, 400), {"detail": {"code": code, "message": message}})


class Tutor:
    """튜터 서비스. 요청 하나 = 그래프 한 번. 성공일 때만 A12가 저장한다."""

    def __init__(self, path: str, client=None, index=None, check=None, given=None, cross=None, shape=None):
        self.store = Store(path)
        self.client = client  # 가짜 모델(시험). 없으면 app/llm 공급자
        self.index = index  # knowledge.index.open_index(...)로 연 벡터 색인. 없으면 온톨로지와 SQLite만으로 돈다
        # check(problem_id, code, quick=False) → 채점 결과 {status, cases[{kind, …}], compile} 또는 None. 풀이 가이드의 정답 코드를 테스트 케이스로 확인한다.
        # 블록 코드 확인은 quick=True로 부른다(효율성 케이스를 빼고 돈다). 케이스의 kind(example, accuracy, efficiency)가 없으면 숨은 케이스로 본다
        self.check = check
        # given(problem_id, language) → {"code"[, "clues", "approach", "steps"]} 또는 None. 정답 코드가 정해진 문제(기본 문제)는 새로 풀지 않고 그 코드로 가이드를 삼는다
        self.given = given
        # cross: 정답 풀이를 실행으로 대조하는 실행기(plan.nodes.cross_check). mode(problem_id) → "function"·"program"(대조하지 않을 문제면 None),
        # run(problem_id, code, brute, maker, bounds) → {status: same|differ|error, …}(채점기 프로세스로만 돌린다), done(problem_id, verdict)(결과를 남긴다).
        # run이 None이면 준비가 대조하지 않고 later(problem_id, report, tiers)에 정석 가이드의 채점 결과와 쓴 급을 맡긴다(대조는 나중에 recheck가 한다)
        self.cross = cross
        # shape(problem_id, language) → {"mode": "function"|"program", "starter": 시작 코드}. 블록 코드 확인이 방식을 코드 모양으로 짐작하지 않고,
        # 풀이 가이드가 시작 코드와 같은 진입 함수 머리를 쓰게 한다. 없으면 함수 방식·시작 코드 없음
        self.shape = shape
        if index is not None:
            self.reindex()

    def reindex(self) -> int:
        """색인이 원본(SQLite)보다 적으면 다시 채운다. 임베딩 모델이 바뀌어 색인이 비었을 때도 이것이 채운다. 넣은 수를 돌려준다."""
        rows = [row for row in self.store.facts() if row["flow"]]
        try:
            if self.index.count() >= len(rows):
                return 0
            for row in rows:
                self.index.put(row["problem_id"], row["spec"], row["flow"], {"algorithm": row["algorithm"], "patterns": row["patterns"], "title": row["title"]})
        except Exception:  # noqa: BLE001 - 색인은 덤이다
            return 0
        return len(rows)

    def close(self) -> None:
        self.store.close()

    def handle(self, request: TutorRequest) -> Outcome:
        with use_llm(self.client) if self.client is not None else nullcontext():
            done = run({"request": request}, self.store, index=self.index, check=self.check, given=self.given, cross=self.cross, shape=self.shape)
        if done.get("error"):
            return _error(done["error"].code, done["error"].message)
        response = done.get("response") or {}
        return Outcome(response.get("status", 200), response.get("body", {}))

    def turn(self, problem_id, mode, event, text=None, block_id=None, code=None, quiet=False, skip=False, own_way=False) -> Outcome:
        """quiet: 블록 코드를 사용자의 말로 대화에 넣지 않는다(채운 마지막 블록의 확인). skip: 확인하지 않고 '확인 전'으로 두고 넘어간다.
        own_way: skip과 함께 남은 블록을 모두 연다('끝까지 내 방식으로 쓰기')."""
        return self.handle(TutorRequest(kind="turn", problem_id=problem_id, mode=mode, event=event, text=text, block_id=block_id, code=code, quiet=quiet, skip=skip,
                                        own_way=own_way))

    def fill(self, problem_id, block_id, filled=None) -> Outcome:
        rows = [item if isinstance(item, FilledBlock) else FilledBlock(id=item["id"], code=item["code"]) for item in filled or []]
        return self.handle(TutorRequest(kind="fill", problem_id=problem_id, block_id=block_id, filled=rows))

    def prepare(self, problem_id) -> Outcome:
        """문항을 등록하거나 열었을 때 미리 불러 둔다: 뼈대(명세·패턴)와 블록 계획을 만들어 저장한다.

        사용자가 문제를 읽는 동안 끝나면 첫 질문은 저장해 둔 질문이라 바로 나온다(모델 0회). 이미 계획이 있으면 아무것도 하지 않는다.
        계획을 만든 뒤 사용자가 코드를 먼저 썼어도 다시 짜지 않고 준비해 둔 순서로 시작한다.
        """
        return self.handle(TutorRequest(kind="prepare", problem_id=problem_id))

    def adopt(self, problem_id, ready: dict) -> bool:
        """미리 만들어 둔 뼈대·풀이 가이드·블록 계획을 그대로 저장한다(기본 문제는 열자마자 시작된다. 모델 0회).

        ready = {"fact": {spec, patterns, skills, size}, "solution": {approach, steps, code, verified}, "plan": 계획(dict)}.
        이미 계획이 있으면 아무것도 하지 않는다.
        """
        ctx = self.store.load(problem_id)
        if ctx is None or ctx.plan is not None:
            return False
        self.store.save_success(ctx, plan_from_json(json.dumps(ready["plan"])), 1, None, [], None, new_plan=True,
                                fact=ready["fact"], solution=Solution(**ready["solution"]))
        return True

    def recheck(self, problem_id, report: dict | None = None, tiers: list | None = None) -> Solution | None:
        """대조 없이 준비해 둔 정석 가이드(서버 준비의 1걸음이 만든 것, 대조 기능이 생기기 전에 등록한 문제)를 한 번 대조한다(계획은 그대로). 결과는 cross.done이 남긴다.
        report·tiers: 그 가이드를 만들 때 맡겨 둔 채점 결과와 쓴 급(cross.later). 없으면 채점하지 못한 까닭을 모르고, 급은 과정의 급 하나로 적는다.
        다시 푼 코드가 대조를 통과해 가이드가 바뀌었으면 새 가이드를 돌려준다(부르는 쪽이 계획을 지우고 새 코드로 다시 짠다). 아니면 None."""
        from .plan.nodes import cross_check

        ctx = self.store.load(problem_id)
        if ctx is None or ctx.canonical is None or self.cross is None or self.check is None or not self.cross.mode(problem_id):
            return None
        ctx = replace(ctx, **self.shape(problem_id, ctx.language)) if self.shape is not None else ctx  # 다시 푼 코드도 시작 코드의 머리를 따른다
        old = ctx.canonical
        with use_llm(self.client) if self.client is not None else nullcontext():
            got, _ = cross_check({"ctx": ctx, "strategy": "fresh"}, Solved(old.approach, old.steps, old.code, old.clues), old.verified, report, self.check, self.cross, tiers)
        if got.code == old.code:
            return None
        return Solution(got.approach.strip(), [step.strip() for step in got.steps if step.strip()], got.code, True, [clue.strip() for clue in got.clues if clue.strip()])

    def debug(self, problem_id, code, report, text=None) -> Outcome:
        """틀린 코드와 채점 결과를 주면 틀린 곳을 찾게 묻는다. text는 그 질문에 대한 사용자 답(없으면 시작)."""
        return self.handle(TutorRequest(kind="debug", problem_id=problem_id, code=code, report=report, text=text))

    def explain(self, problem_id) -> Outcome:
        return self.handle(TutorRequest(kind="explain", problem_id=problem_id))

    def feedback(self, problem_id) -> Outcome:
        return self.handle(TutorRequest(kind="feedback", problem_id=problem_id))

    def session(self, problem_id, mode=None) -> Outcome:
        """mode="chair"면 지금 블록 이름도 가린다(의자 화면용)."""
        ctx = self.store.load(problem_id)
        if ctx is None:
            return _error("not_found", "문제를 찾지 못했어요.")
        return Outcome(200, session_body(ctx, mode))

    def feedback_get(self, problem_id) -> Outcome:
        if self.store.load(problem_id) is None:
            return _error("not_found", "문제를 찾지 못했어요.")
        body = self.store.get_feedback(problem_id)
        return Outcome(200, body) if body is not None else _error("not_found", "피드백이 없습니다.")
