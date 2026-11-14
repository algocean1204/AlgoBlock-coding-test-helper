"""시험 도우미. 가짜 모델과, 저장소 없이 도는 파이프라인(문맥 불러오기·저장을 바꿔 끼움)."""

from dataclasses import replace
from functools import cache
from pathlib import Path

from ..llm import FakeLlm, use_llm
from ..main import build, default_agents, run
from ..state import Block, BlockPlan, ChatMessage, MainState, Solution, TutorContext, TutorRequest

ROOT = Path(__file__).resolve().parents[1]  # graph 폴더

PROBLEM = "작은 도서관은 누군가 책을 빌려 갈 때마다 그 책의 제목을 기록합니다. 대출 기록을 일어난 순서대로 담은 문자열 배열 loans와 정수 k가 주어집니다. 제목이 같으면 같은 책입니다.\n어떤 책이 k번째로 빌려지는 바로 그때, 사서는 그 책을 추천 서가에 꽂습니다. 한 번 꽂은 책은 그 뒤에 더 빌려져도 다시 꽂지 않습니다.\n추천 서가에 꽂힌 책의 제목을 꽂힌 순서대로 담은 배열을 return 하도록 solution 함수를 완성하세요."

# 꼴이 다른 문제 글(시험이 한 문제의 꼴에 기대지 않게): 표준 입출력 방식 하나, Python이 아닌 언어의 함수 방식 하나
PROGRAM_PROBLEM = ("첫째 줄에 정류장 수 N이 주어지고, 둘째 줄에 정류장마다 탄 사람 수가 공백으로 주어진다.\n"
                   "탄 사람이 가장 많은 정류장의 번호(1부터)를 출력한다. 가장 많은 정류장이 여럿이면 앞 번호를 출력한다.")
KOTLIN_PROBLEM = "정수 배열 heights와 정수 limit이 주어집니다. heights에서 limit보다 큰 값의 개수를 return 하도록 solution 함수를 완성하세요."

SECTIONS = [
    {"title": "문제에서 읽을 것", "body": "읽을 것"},
    {"title": "흐름", "body": "흐름"},
    {"title": "블록이 놓이는 순서", "body": "순서"},
    {"title": "블록별 설명", "body": "이어서"},
]

HINTS1 = ["책마다 무엇을 기록해 둬야 할까요?", "'제목이 같으면 같은 책입니다'를 보면 제목마다 무엇을 따로 세어야 할까요?", "loans가 owl, tide, owl이라면 무엇을 세야 할까요?"]
HINTS2 = ["세어 둔 횟수는 어떻게 쓰일까요?", "'k번째로 빌려지는 바로 그때'를 잡으려면 횟수를 언제 견줘야 할까요?", "k가 2이고 owl, tide, owl이라면 어디서 꽂을까요?"]


def block(number: int, name: str, reference: str, kind: str = "var_from_problem", **extra) -> Block:
    return Block(id=f"b{number}", kind=kind, name=name, goal=f"목표-{name}", reference=reference, **extra)


def as_dict(item: Block) -> dict:
    return {"id": item.id, "kind": item.kind, "name": item.name, "goal": item.goal, "reference": item.reference,
            "checks": item.checks, "hints": item.hints}


def drafted(blocks: list[dict], algorithm: str = "hash", out_of_scope: bool = False) -> dict:
    return {"algorithm": algorithm, "out_of_scope": out_of_scope, "blocks": blocks}


def two() -> list[Block]:
    """뒤 블록 이름 NEXT_SECRET, 참고 코드 REF_ONE·REF_TWO는 말풍선에 나가면 안 되는 표식이다."""
    return [block(1, "입력받기", "REF_ONE"), block(2, "NEXT_SECRET", "REF_TWO", "loop")]


def hinted() -> list[Block]:
    one, second = two()
    return [replace(one, checks=["글자별로 센다", "같은 글자가 여러 번 나오는 경우를 다룬다"], hints=list(HINTS1)),
            replace(second, checks=["앞에서부터 다시 훑어 한 번 나온 글자를 찾는다"], hints=list(HINTS2))]


def thinking() -> list[Block]:
    """첫 블록이 조건 블록인 계획(근거 질문은 반복·조건·분기 블록에서만 한다)."""
    one, second = hinted()
    return [replace(one, kind="condition"), second]


def planned(blocks: list[Block], strategy: str = "fresh", score: int | None = None, algorithm: str = "hash") -> BlockPlan:
    return BlockPlan(strategy=strategy, score=score, blocks=blocks, algorithm=algorithm)


def context(**kwargs) -> TutorContext:
    base = dict(problem_id="p1", problem_text=PROBLEM, language="python", spec="문자열 배열 둘, 남는 원소 하나")  # 뼈대가 있으면 다시 뽑지 않는다
    base.update(kwargs)
    return TutorContext(**base)


def make_state(kind: str, ctx: TutorContext, guide: bool = True, **kwargs) -> MainState:
    """guide: 블록 코드 확인·채우기는 검증된 풀이 가이드가 있어야 계획 코드와 이어 돌린다(없으면 guide=False)."""
    if guide and ctx.solution is None and ctx.plan is not None and (kind == "fill" or kwargs.get("event") == "block_filled"):
        ctx.solution = Solution("센다", ["센다"], "\n".join(b.reference for b in ctx.plan.blocks), True, [])
    return {"request": TutorRequest(kind=kind, problem_id=ctx.problem_id, **kwargs), "ctx": ctx, "open_count": ctx.open_count}


def service(text: str, block_index: int, message_id: str = "m1", move: str | None = "open") -> ChatMessage:
    return ChatMessage(id=message_id, role="service", text=text, at="2026-10-15T00:00:00+09:00", block_index=block_index, move=move)


def user(text: str, block_index: int, message_id: str = "u1") -> ChatMessage:
    return ChatMessage(id=message_id, role="user", text=text, at="2026-10-15T00:00:00+09:00", block_index=block_index)


def _keep_context(state: MainState) -> dict:
    return {"open_count": state["ctx"].open_count}


def _no_save(state: MainState) -> dict:
    return {"response": {"status": 200, "body": {"stub": True}}}


@cache
def pipeline():
    """A2·A12를 바꿔 끼운 튜터 그래프. 문맥은 시험이 직접 넣는다."""
    return build({**default_agents(), "context": _keep_context, "save": _no_save})


def go(state: MainState, scripts: dict, check=None):
    fake = FakeLlm(scripts)
    with use_llm(fake):
        return run(state, store=None, compiled=pipeline(), check=check), fake


def tasks(fake) -> list[str]:
    return [call["task"] for call in fake.calls]


def prompt(fake, task: str) -> str:
    return "\n".join(item["content"] for call in fake.calls if call["task"] == task for item in call["messages"])
