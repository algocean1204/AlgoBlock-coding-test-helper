"""튜터 그래프가 주고받는 데이터. 괄호 안은 데이터 사전의 이름이다.

그래프 노드는 바뀐 필드만 돌려준다. 저장소는 A2(context)와 A12(save)만 만진다.
"""

from dataclasses import dataclass, field
from typing import Any, Required, TypedDict

BLOCK_KINDS = ("var_from_problem", "var_during", "loop", "condition", "branch")

EXPLAIN_TITLES = ("문제에서 읽을 것", "흐름", "블록이 놓이는 순서", "블록별 설명")

KINDS = ("explain", "turn", "followup", "fill", "feedback", "debug", "prepare")


@dataclass
class ErrorInfo:
    """오류"""

    code: str
    message: str


@dataclass
class Block:
    """블록 계획.블록[]"""

    id: str
    kind: str
    name: str
    goal: str
    reference: str = ""  # 이 블록의 참고 코드. 풀이 가이드가 있으면 그 코드의 lines 구간을 그대로 옮긴 것이다
    checks: list[str] = field(default_factory=list)  # 신호 1–3개. 1번이 핵심
    hints: list[str] = field(default_factory=list)  # 의자 질문 0 open, 1 clue, 2 trace
    lines: list[int] = field(default_factory=list)  # 풀이 가이드 코드에서 이 블록이 맡은 줄 [처음, 끝](1부터). 가이드가 없으면 빈 목록


@dataclass
class BlockState:
    """블록 판정 기록"""

    block_id: str
    code: str
    code_hash: str
    verdict: str  # Y, N 또는 ?(확인 전: 앞 블록이 바뀌어 통과를 물렸거나, 다시 확인이 실패했거나, 이어 돌려 통과하지 못한 채운 블록, 실행하지 못하고 통과한 블록)
    miss: int | None = None
    tries: int = 1
    renames: list[list[str]] = field(default_factory=list)  # 이 블록이 이름 바꾸기 표에 더한 짝 [[내 이름, 계획 이름], …](통과했을 때만)


@dataclass
class BlockPlan:
    """블록 계획"""

    strategy: str
    score: int | None
    blocks: list[Block]
    algorithm: str = ""
    out_of_scope: bool = False
    link: str = ""  # 사용자가 전에 풀어 본 같은 구조 문항 한 줄(제목: 흐름). 떠올리게 하는 말에만 쓴다. 풀이를 정하지 않는다


@dataclass
class Solution:
    """풀이 가이드: 문제 글만 보고 만든 분석(단서 → 풀이 방향 → 단계 → 정답 코드). 블록은 이 코드를 순서대로 나눈 것이다.

    문제를 처음 넣을 때 한 번 만들어 고정한다(정석 가이드). 같은 문제를 여러 번 풀어도 같은 방향으로 배우게 하려는 것이다.
    """

    approach: str  # 풀이 방향 2~4문장
    steps: list[str]  # 순서 있는 단계(한 줄씩)
    code: str  # 전체 정답 코드
    verified: bool | None = False  # 등록된 테스트 케이스를 채점기로 확인한 결과: True 통과, False 통과하지 못함, None 채점하지 못함(도구·케이스가 없거나 인자 형을 다루지 못함)
    clues: list[str] = field(default_factory=list)  # 단서: 문제 글의 어떤 말·제한에서 무엇을 읽어 내는가(한 줄씩)


@dataclass
class Section:
    title: str
    body: str


@dataclass
class Explain:
    sections: list[Section]


@dataclass
class ChatMessage:
    id: str
    role: str  # user 또는 service
    text: str
    at: str
    block_index: int | None = None
    quote_id: str | None = None
    move: str | None = None  # 질문 유형(서비스 말). 사용자 말에는 블록 코드 확인의 판정 표시(talk_rules.CHECKED + Y·N·?)만


@dataclass
class FollowupThread:
    quote_id: str
    messages: list[ChatMessage] = field(default_factory=list)


@dataclass
class Submission:
    id: str
    source: str
    ok: bool


@dataclass
class FilledBlock:
    id: str
    code: str


@dataclass
class DebugState:
    """디버그 진단 기록. 같은 코드면 다시 진단하지 않는다"""

    code_hash: str
    kind: str  # syntax, runtime, logic
    line: int
    cause: str
    fixed_line: str
    step: int = 0
    pitfall: str = ""  # 온톨로지 함정 id(없으면 빈 글)
    trap: str = ""  # 고른 언어 함정 id(묶음의 traps. 없으면 빈 글). 피드백이 이어 받는다


@dataclass
class TutorRequest:
    """튜터 요청"""

    kind: str
    problem_id: str = ""
    mode: str | None = None
    event: str | None = None
    text: str | None = None
    block_id: str | None = None
    code: str | None = None
    quote_id: str | None = None
    filled: list[FilledBlock] = field(default_factory=list)
    report: dict | None = None  # 디버그: 채점 결과 {status, cases[{id, input, expected, got, error, status}], compile}
    quiet: bool = False  # 블록 코드를 사용자의 말로 대화에 넣지 않는다(채운 마지막 블록의 확인)
    skip: bool = False  # 블록 코드 확인을 하지 않고 '확인 전'으로 둔 채 다음 블록으로 넘어간다(모델·실행 0회)
    own_way: bool = False  # skip과 함께: 남은 블록을 모두 연다('끝까지 내 방식으로 쓰기'. 블록마다의 확인을 그만 받는다)


@dataclass
class TutorContext:
    """문항 문맥"""

    problem_id: str
    problem_text: str
    language: str
    direct_code: str = ""
    title: str = ""
    plan: BlockPlan | None = None
    open_count: int = 0
    chair: list[ChatMessage] = field(default_factory=list)
    guide: list[ChatMessage] = field(default_factory=list)
    followups: list[FollowupThread] = field(default_factory=list)
    explain: Explain | None = None
    latest_submission: Submission | None = None
    block_states: dict[str, BlockState] = field(default_factory=dict)
    debug: list[ChatMessage] = field(default_factory=list)
    debug_state: DebugState | None = None
    spec: str = ""  # 이야기를 걷어 낸 명세(문항 뼈대)
    patterns: list[str] = field(default_factory=list)  # 온톨로지 패턴 id
    skills: list[str] = field(default_factory=list)  # 온톨로지 구현 기술 id
    size: int = 0  # 가장 큰 입력 크기
    frequent_pitfalls: list[tuple[str, int]] = field(default_factory=list)  # 이 사용자가 여러 문항에서 밟은 함정(id, 횟수)
    level: str = "middle"  # 학습자 눈높이(beginner, middle, advanced). 제출 기록에서 볼 때마다 센다
    solved: dict[str, int] = field(default_factory=dict)  # 유형 → 통과한 다른 문항 수
    library: list[dict] = field(default_factory=list)  # 다른 문항 {problem_id, title, spec, algorithm, patterns, flow, passed, tried}
    solution: Solution | None = None  # 지금 계획이 따르는 풀이 가이드(사용자 방법으로 다시 짰으면 그 방법의 가이드, 아니면 정석 가이드)
    canonical: Solution | None = None  # 정석 가이드(문제마다 하나. 사용자 방법으로 다시 짜도 덮어쓰지 않는다)
    failed_submissions: list[str] = field(default_factory=list)  # 이 문항에서 통과하지 못한 제출의 결과 종류(오래된 것부터). 피드백이 막힌 지점을 적는다
    hints_seen: int = 0  # 이 문항에서 본 힌트 수(AI 없이 본 것)
    mode: str = "function"  # 문항의 푸는 방식(function·program). 서버가 아는 값을 받는다(shape)
    starter: str = ""  # 이 언어의 시작 코드(풀이 가이드의 진입 함수 머리를 이것과 같게 묶는다. 없으면 빈 글)
    many_answers: bool = False  # 등록할 때 '답이 여럿일 수 있음'을 켰다(값이 다르면 맞는지 가릴 수 없다). 서버가 아는 값을 받는다(shape)
    traps: list[dict] = field(default_factory=list)  # 이 문제·언어에서 증명된 언어 함정 [{id, what, fix, code, right, fails 또는 varies}]. 기본 문제만. 서버가 아는 값을 받는다(shape)


@dataclass
class Verdict:
    """판정. [check] 한 줄을 읽은 값"""

    ok: bool
    miss: int | None = None
    basis: str | None = None  # 근거 수준 t, e, g
    score: int | None = None
    malformed: bool = False
    other: bool = False  # D: 계획과 다르지만 문제가 풀리는 방법을 말했다
    aside: str = ""  # A: 답·답 코드를 달라는 요청, O: 문제와 무관한 말, W: 낱말·개념의 뜻을 묻는 말(의자·가이드 말 판정만)
    seen: str = ""  # 블록 코드 확인이 통과하지 못했을 때 실행에서 본 것 한 줄(오답 값, 오류, 괄호 수)
    hint: bool = True  # 거짓이면 그 실패와 상관없는 저장 힌트를 붙이지 않는다(문법·실행 오류, 괄호·들여쓰기 안내, 이름 찾기 실패)
    ran: bool = True  # 블록 코드 확인: 거짓이면 실행하지 못해 모델이 코드를 읽고 본 판단이다(통과여도 '확인 전'으로 보이고 그렇다고 말한다)
    unsure: bool = False  # 블록 코드 확인: 통과도 '이어지지 않아요'도 아니다 — 이어 돌려 결론까지 가지 못해 '확인 전'으로 둔다(틀린 수에 넣지 않는다)


@dataclass
class TurnContext:
    """턴 문맥"""

    index: int
    block: Block
    last_question: str
    recent: list[str]
    moves_used: list[str]
    event: str
    text: str
    followed_before: bool = False  # 이 문항에서 이미 사용자 방법으로 다시 짠 적이 있다
    basis_asked: bool = False  # 이 문항에서 근거 질문을 이미 했다
    previous: str = ""  # 이 블록에서 사용자가 바로 앞에 한 말(없으면 빈 글)
    tipped: bool = False  # 이 블록에서 '이 블록 채우기' 안내(FILL_TIP)를 이미 붙였다
    hints_seen: int = 0  # 이 블록의 저장 힌트 가운데 이미 낸 수(다음 번호를 고른다)


@dataclass
class MovePlan:
    """질문 계획"""

    move: str
    target: int
    advance: bool
    lead: str = ""  # 이음말 또는 앞말
    saved: str | None = None
    missing_signal: str = ""


@dataclass
class Abstract:
    """문항 뼈대: 이야기를 걷어 낸 명세와 온톨로지 패턴"""

    spec: str
    patterns: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)  # 구현 기술 id
    size: int = 0  # 제한사항에서 가장 큰 입력 크기(모르면 0)
    level: Any = 0  # 단계 1~5(모르면 0). 등록한 문제의 목록에 보인다. 모델 출력은 모양을 따지지 않고 받아("2", 2.0, null로 뼈대를 잃지 않게) plan.nodes.abstract가 정수로 바꾼다
    tags: list[str] = field(default_factory=list)  # 쓰는 방법(온톨로지 기법 id) 2~4개


class MainState(TypedDict, total=False):
    """요청 상태"""

    request: Required[TutorRequest]
    ctx: TutorContext
    plan: BlockPlan | None  # 새 계획
    result: dict | None  # 에이전트 결과 → 검사한 결과
    open_count: int  # 열린 블록 수
    error: ErrorInfo | None
    strategy: str | None
    score: int | None
    direction_ok: bool | None
    draft: object  # 블록 초안, 해설 초안, 피드백 초안
    turn: TurnContext
    verdict: Verdict
    move: MovePlan
    reply_draft: str  # 말풍선 초안
    block_check: BlockState | None  # 블록 판정 기록
    block_fixes: list  # 다시 고른 앞 블록의 판정 기록(짝을 새 차례로 고쳐 쓴 것)
    withdrawn: list  # 이 블록의 글이 바뀌어 통과를 물린 뒤 블록 id
    renamed: list  # 블록 코드가 계획과 다르게 부른 이름 가운데 이번에 처음 알리는 짝 [[내 이름, 계획 이름], …](통과했을 때만)
    changes: dict  # 저장할 변경
    response: dict  # 튜터 응답 {status, body}
    abstract: Abstract | None  # 이번 요청에서 뽑은 문항 뼈대
    recall: dict | None  # 불러온 지식 {spec, patterns[], similar[], weak[]}
    debug_state: DebugState | None  # 저장할 디버그 진단
    follow: str | None  # 사용자가 말한 다른 풀이 방법(이 방법으로 블록을 다시 짠다)
    solution: Solution | None  # 이번 요청에서 만든 풀이 가이드
    link: str  # 관문을 통과한 지난 문항 한 줄(없으면 빈 글)
    replanned: str | None  # followed(다시 짰다) 또는 rejected(그 방법으로는 풀리지 않아 계획 유지)
    rule_cut: bool  # 모델의 줄 구간을 쓸 수 없어 블록을 규칙으로 잘랐다(계획 strategy가 rule_cut)


# 모델 출력 모양(JSON 모드)


@dataclass
class Solved:
    """풀이 가이드 초안(모델 출력)"""

    approach: str
    steps: list[str]
    code: str
    clues: list[str] = field(default_factory=list)
    followed: bool = True  # 사용자 방법 따르기에서: 그 방법으로 풀려서 따랐는가


@dataclass
class LabeledSolved(Solved):
    """정석 가이드 초안: 쓴 코드로 정한 태그·단계도 받는다(그것을 물을 때만 이 모양으로 받는다. 키 안내가 묻는 것과 같게).
    둘은 덤이라 모양을 따지지 않고 받는다(null, "2", 2.0, "bfs"로 가이드 전체를 잃지 않게). 쓸 수 있는 값만 plan.nodes.guide_labels가 고른다."""

    tags: Any = None  # 이 코드가 쓰는 방법(온톨로지 기법 id 목록)
    level: Any = None  # 이 코드로 본 단계 1~5


@dataclass
class Written:
    """코드 한 편(모델 출력): 단순 풀이"""

    code: str


@dataclass
class Bound:
    """케이스 생성기가 적은 제한사항 하나(모델 출력). 생성된 입력을 앱이 규칙으로 검사한다(생성기 코드를 앱에서 돌리지 않는다)"""

    arg: int  # 몇 번째 인자(0부터). 표준 입출력 방식은 0(입력 글 전체)
    low: int | None = None  # 그 인자 안의 모든 수의 가장 작은 값
    high: int | None = None  # 가장 큰 값
    shortest: int | None = None  # 그 인자(배열·문자열)의 가장 짧은 길이
    longest: int | None = None  # 가장 긴 길이


@dataclass
class CaseMaker:
    """케이스 생성기(모델 출력): small·edge·tricky·large 함수를 담은 파이썬 코드와 제한사항(tricky는 없어도 된다)"""

    code: str
    bounds: list[Bound] = field(default_factory=list)


@dataclass
class DraftedBlocks:
    algorithm: str
    out_of_scope: bool
    blocks: list[Block]
    followed: bool = True  # 사용자 방법 따르기에서: 그 방법으로 풀려서 따랐는가


@dataclass
class BlockHints:
    id: str
    hints: list[str]
    name: str = ""  # 아래 셋은 규칙으로 자른 블록의 이름·목표·신호를 받을 때만
    goal: str = ""
    checks: list[str] = field(default_factory=list)


@dataclass
class MendedHints:
    """원칙을 어겨 다시 받은 블록 질문(모델 출력)"""

    blocks: list[BlockHints]


@dataclass
class Diagnosis:
    """디버그 진단(모델 출력)"""

    kind: str
    line: int
    cause: str
    fixed_line: str
    pitfall: str = ""
    trap: str = ""  # 내놓은 언어 함정 후보 가운데 고른 id(없으면 빈 글)
    opening: str = ""  # 사용자에게 보일 첫 질문(실패 입력과 코드의 단서를 짚는다). 비거나 검사에 걸리면 정해진 글


@dataclass
class Reply:
    text: str


@dataclass
class BlockCode:
    code: str


@dataclass
class Analysis:
    analysis: str
    similar_hint: str
    advice: str


@dataclass
class PageText:
    text: str
    readable: bool  # 거짓이면 그림에서 글을 읽지 못했다(그때의 text는 문제 글이 아니다). 빠진 답은 형식 실패다(읽었다고 짐작하지 않는다)


def fail(code: str, message: str) -> dict:
    return {"error": ErrorInfo(code, message)}
