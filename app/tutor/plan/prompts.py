"""블록 초안 프롬프트. 순서 유지가 아니면 사용자 코드를 넣지 않는다."""

import json
from pathlib import Path

from ..common.scope import OUTSIDE_PROBLEMS, PRINCIPLES, SOLVE_SCOPE
from ..common.solution import solution_of
from ..debug.rules import numbered
from ..knowledge.ontology import pattern_list, size_table, skill_list, technique_list
from ..llm import cached_user
from ..state import LabeledSolved, MainState, Solved

GUIDE = (Path(__file__).with_name("guide.md")).read_text(encoding="utf-8")  # 참고용. 지켜야 하는 것은 rules.py만

KIND_TEXT = "\n".join(
    [
        "종류는 블록의 가장 바깥 구조로 정한다.",
        "- var_from_problem: 문제에서 바로 나오는 값을 변수에 담는다(입력의 길이, 입력에서 바로 읽는 값, 문제 글에 적힌 상수)",
        "- var_during: 풀이 중에 만들어 쓰는 변수(빈 키-값 표·스택·덱·힙·표, 누적 값, 답을 담을 변수). return만 있는 블록도 풀이 중에 만든 값을 돌려주면 이것",
        "- loop: for/while로 시작하는 블록",
        "- condition: 조건을 따져 고르는 일(if 한 덩어리)",
        "- branch: 경우를 나눠 서로 다른 일을 한다(if와 else로 여러 갈래로 나누기, 일찍 돌려주기와 그 밖)",
        "- 도우미 함수 정의 블록은 그 함수가 주로 하는 일의 종류",
    ]
)

STRATEGY_TEXT = {
    "fresh": "새로 짜기: 볼 코드가 없다. 정석 흐름으로 블록을 짠다.",
    "canonical": "정석으로: 사용자 코드의 방향이 맞지 않거나 점수가 낮다. 사용자 코드를 따르지 말고 정석 흐름으로 짠다.",
    "keep_flow": "순서 유지: 사용자 코드의 방향이 맞다. 사용자 코드의 순서를 유지해 블록을 짜고, 빠진 블록만 채운다.",
    "follow": "사용자 방법 따르기: 사용자가 말한 방법으로 제한사항의 입력 크기 안에서 모든 입력이 맞게 풀리면, 그 방법의 순서대로 블록을 짜고 followed를 true로 한다. "
    "틀린 답이 나오는 입력이 있거나 시간 안에 못 돌면 followed를 false로 하고 정석 흐름으로 짠다.",
}

# 좋은 답의 힌트는 HINT_RULES를 지킨다(열린 질문 → 문제 글 한 문장 인용 → 작은 예시 따라가기, 예/아니요로 답할 수 없는 질문)
_EXAMPLE_HINTS = ('"hints":["꽂히는 순서를 맞추려면 대출 기록을 어떤 순서로 하나씩 봐야 할까요?",'
                  '"\'loans의 길이는 1 이상 100,000 이하입니다\'를 보면 기록을 몇 번이나 훑는 방법이어야 할까요?",'
                  '"tide, tide가 차례로 들어오면 첫 번째와 두 번째 tide를 볼 때 그 제목의 횟수는 각각 얼마가 되어야 할까요?"]}\n'
                  '나쁜 답의 힌트: "좋아요! count 표를 만들어 보세요."(칭찬, 코드 이름, 질문이 아님)')
# 예의 reference는 언어마다 실제로 컴파일·실행되는 것을 확인한 같은 뜻의 코드다. 없는 언어에는 reference 예를 넣지 않는다
_EXAMPLE_REFERENCE = {
    "python": "for title in loans:\n    count[title] = count.get(title, 0) + 1",
    "java": "for (String title : loans) {\n    count.put(title, count.getOrDefault(title, 0) + 1);\n}",
    "javascript": "for (const title of loans) {\n    count[title] = (count[title] ?? 0) + 1;\n}",
    "cpp": "for (const string& title : loans) {\n    count[title] += 1;\n}",
    "rust": "for title in &loans {\n    *count.entry(title).or_insert(0) += 1;\n}",
}


def example(language: str) -> str:
    code = _EXAMPLE_REFERENCE.get(language)
    return (
        '좋은 답의 블록 하나: {"id":"b2","kind":"loop","name":"대출 횟수 세기","goal":"대출 기록을 일어난 순서대로 한 번만 훑으며 그 제목의 횟수를 1 올린다",'
        + (f'"reference":{json.dumps(code)},' if code else "")
        + '"checks":["대출 기록을 처음부터 끝까지 한 권씩 차례로 훑는다","처음 보는 제목은 0에서 시작해 횟수를 1 올린다"],'
        + _EXAMPLE_HINTS
    )


EXAMPLE_LINES = (
    '좋은 답의 블록 하나: {"id":"b2","kind":"loop","name":"대출 횟수 세기","goal":"대출 기록을 일어난 순서대로 한 번만 훑으며 그 제목의 횟수를 1 올린다","lines":[4,5],'
    '"checks":["대출 기록을 처음부터 끝까지 한 권씩 차례로 훑는다","처음 보는 제목은 0에서 시작해 횟수를 1 올린다"],'
    + _EXAMPLE_HINTS
)

METHOD_TEXT = (
    "방법 고르기: 제한사항의 입력 크기 안에서 시간 안에 도는 가장 단순한 방법을 고른다(대략 1초에 1억 번 연산). "
    "예: 길이 1,000 이하에서 두 개를 고르는 문제는 이중 반복 완전탐색이면 충분하다. 더 빠른 방법은 단순한 방법이 시간을 넘을 때만 쓴다."
)

SOLVE_SYSTEM = (
    "너는 코딩테스트 문제의 정답 풀이를 쓰는 풀이자다. 문제 글과 제한사항만 보고 푼다(다른 문제의 풀이를 떠올려 끼워 맞추지 않는다). "
    "이 결과는 튜터가 풀이 순서(블록)를 짜는 바탕이 되고, 풀이 방향·단서·단계는 사용자가 보는 해설에도 실린다. 코드는 테스트 케이스로 채점해 통과해야 쓰인다. "
    + OUTSIDE_PROBLEMS
)

SOLVE_STRATEGY = {
    "fresh": "정석 풀이를 쓴다.",
    "canonical": "정석 풀이를 쓴다(사용자 코드는 방향이 맞지 않아 따르지 않는다).",
    "keep_flow": "사용자 코드의 방향이 맞다. 사용자 코드의 방법과 순서를 그대로 살려, 빠지거나 틀린 곳만 고친 올바른 전체 코드를 쓴다.",
    "follow": "사용자가 말한 방법으로 제한사항의 입력 크기 안에서 모든 입력이 맞게 풀리면, 그 방법으로 풀고 followed를 true로 한다. "
    "틀린 답이 나오는 입력이 있거나 시간 안에 못 돌면 followed를 false로 하고 정석 풀이를 쓴다.",
}


# 시작 코드를 따르게 하는 말. 표준 입출력에서 입력 전체를 토큰으로 쪼개 커서를 단계마다 넘기면, 시작 코드대로 읽는 사용자 블록과 이어 돌릴 수 없었다
STARTER_NOTE = {
    "function": "시작 코드(사용자가 받는 코드다. 진입 함수의 머리 — 함수 이름, 인자 이름과 차례 — 를 이것 그대로 쓴다):",
    # 시작 코드는 두 모양이다: 필요할 때마다 읽는 것(한 줄씩, 값 하나씩)과 입력 전체를 한 번에 읽는 것. 언어 이름이 아니라 그 모양으로 말한다
    "program": "시작 코드(사용자가 받는 코드다. 입력을 읽는 방법을 이것 그대로 따른다. 시작 코드가 필요할 때마다 읽는 모양(한 줄씩, 값 하나씩)이면 입력은 그 값이 필요한 단계에서 읽는다. "
               "시작 코드가 입력 전체를 한 번에 읽으면 그 글을 줄 목록으로 한 번만 나누고, 각 단계는 문제 글의 양(N, Q 등)으로 몇째 줄인지 정해 그 줄을 읽는다. "
               "읽은 값은 문제 글이 이름 붙인 양(크기, 격자, 질문 수 등)의 변수에 담는다. 단계를 넘어 이어 쓰는 값은 그 변수들(과 줄 목록)뿐이다: "
               "읽은 위치(커서)를 여러 단계에 걸쳐 옮기지 않는다):",
}


def solved_schema(state: MainState, given: str = "") -> type:
    """풀이 가이드의 답 모양. 정석 가이드만 문제의 태그·단계를 함께 묻는다(사용자 코드·방법을 따른 가이드, 정해 둔 코드의 설명은 묻지 않는다).
    프롬프트의 안내와 공급자에 붙는 키 안내가 같은 것을 묻게, 둘 다 이것으로 정한다."""
    return LabeledSolved if (state.get("strategy") or "fresh") in ("fresh", "canonical") and not given else Solved


def solve_messages(state: MainState, retry: str = "", given: str = "") -> list[dict]:
    """풀이 가이드(A4). 문제 글만 준다: 지난 문항, 패턴, 사용자 기록을 넣지 않는다(다른 문제의 풀이가 끼어들지 않게).
    푸는 방식은 등록한 방식(SHAPE[mode])을 따르고, 시작 코드가 있으면 그 틀을 따르게 한다(단순 풀이·생성기와 같은 기준):
    함수 방식은 진입 함수 머리, 표준 입출력은 입력 읽기 꼴(블록 사이를 잇는 값이 커서가 아니라 문제 글의 양이 되게).
    given은 정해 둔 정답 코드다: 코드를 새로 쓰지 않고 그 코드의 단서·방향·단계만 쓰게 한다.
    정석 가이드는 쓴 코드로 문제의 태그·단계도 함께 받는다(호출 수는 그대로. 기법 목록은 문제마다 같은 목록이다)."""
    ctx = state["ctx"]
    strategy = state.get("strategy") or "fresh"
    lines = [
        f"문제:\n{ctx.problem_text}",
        f"언어:{ctx.language}",
        "쓸 수 있는 기법(이 안에서 푼다):",
        SOLVE_SCOPE,
        METHOD_TEXT,
        "입력 크기 경험칙:",
        size_table(),
        f"전략: {SOLVE_STRATEGY[strategy]}",
    ]
    if strategy == "keep_flow":
        lines.append(f"사용자 코드:\n{ctx.direct_code}")
    if strategy == "follow":
        lines.append(f"사용자가 말한 방법:\n{state.get('follow') or ''}")
        if ctx.solution is not None:
            lines.append(f"지금 풀이 방향: {ctx.solution.approach}")
            lines.append("사용자가 말한 방법이 지금 풀이와 같은 방법이면(뒤 단계의 내용을 미리 말한 것 포함) 다시 풀 필요가 없다. followed를 false로 한다.")
    lines += [
        "clues: 문제 글에서 풀이를 정하는 단서 2~4개. 한 줄에 하나, '문제 글의 말이나 제한사항 → 그래서 무엇이 필요한가' 꼴로 쓴다. "
        "문제 글의 말은 작은따옴표 안에 한 글자도 바꾸지 않고 옮긴다. 입력 크기 제한이 방법을 가르면 그것도 단서다.",
        "approach: 풀이 방향 2~4문장. 단서에서 이어서, 무엇을 기억해 두고 어떤 순서로 보는지, 왜 그 방법인지. 초보자가 읽을 쉬운 말로 쓴다.",
        "steps: 풀이를 위에서 아래로 따라가는 단계 3~7개. 한 단계는 한 줄('무엇을 한다(왜)')이고 코드의 이어진 줄 묶음 하나와 맞는다.",
        f"code: 전체 정답 {ctx.language} 코드. {SHAPE[ctx.mode]}{' Java는 public class Main.' if ctx.mode == 'program' else ''} 코딩테스트를 막 시작한 사람이 읽을 수 있게 쓴다: 한 줄에 한 가지 일, "
        "줄임 표현(컴프리헨션, 람다, 한 줄 조건식)과 낯선 내장 함수를 피하고, 변수 이름은 뜻이 보이게 짓는다. 주석과 빈 줄을 쓰지 않는다. 입력으로 받은 값을 바꾸지 않는다.",
    ]
    labeled = solved_schema(state, given) is LabeledSolved
    if labeled:  # 글보다 먼저 정하면 문제 글의 분류 표시에 끌렸다: 쓴 코드가 실제로 하는 일로 정한다
        lines += ["tags: 아래 기법 목록에서 위 code가 실제로 쓰는 방법의 id 2~4개. code에 없는 방법은 쓰지 않는다(목록에 없는 낱말도 쓰지 않는다).", technique_list(ctx.language),
                  LEVEL_TEXT + " 위 code가 쓰는 방법으로 정한다."]
    lines.append('JSON {"clues": ["..."], "approach", "steps": ["..."], "code"'
                 + (', "tags": [id], "level"}' if labeled else ', "followed": true 또는 false}' if strategy == "follow" else "}"))
    if ctx.starter.strip() and not given:  # 사용자가 받는 시작 코드와 같은 틀(함수 머리, 입력 읽기)이어야 블록이 이어진다
        lines.append(f"{STARTER_NOTE[ctx.mode]}\n{ctx.starter}")
    if retry:
        lines.append(f"앞서 쓴 코드는 채점에서 틀렸다. 원인을 찾아 고친 전체 코드를 다시 쓴다.\n{retry}")
    if given:
        lines.append("정답 코드는 아래로 정해져 있다(채점을 통과한 코드다). 코드를 새로 쓰거나 바꾸지 않는다. 이 코드가 푸는 방법 그대로 clues, approach, steps를 쓰고 "
                     f"(steps는 이 코드의 이어진 줄 묶음과 위에서 아래로 맞는다), code에는 빈 글을 적는다.\n정답 코드:\n{given}")
    return [{"role": "system", "content": SOLVE_SYSTEM}, cached_user(lines, 2)]


GATE_SYSTEM = (
    "너는 두 코딩테스트 문제가 같은 구조인지 판정한다. 같은 구조란 한 문제의 풀이 흐름을 다른 문제에 그대로 쓸 수 있다는 뜻이다. "
    "글이 닮았어도 조건 하나(음수 허용, 개수를 세는가 있는지만 보는가, 이어진 구간인가, 순서가 중요한가 등)가 달라 풀이가 바뀌면 다른 구조다. 판정만 한다."
)


def gate_messages(spec: str, approach: str, other: dict) -> list[dict]:
    lines = [
        f"지금 문제의 명세: {spec}",
        f"지금 문제의 풀이 방향: {approach}",
        f"지난 문제의 명세: {other['spec']}",
        f"지난 문제의 풀이 흐름: {other['flow']}",
        "지난 문제의 풀이 흐름을 지금 문제에 그대로 쓸 수 있으면 Y, 아니면 N. 한 글자만 쓴다.",
    ]
    return [{"role": "system", "content": GATE_SYSTEM}, {"role": "user", "content": "\n".join(lines)}]


# 불러온 지식(온톨로지, 닮은 문항, 사용자 기록)은 보조 수단이다. 근거가 아니라 참고서처럼 쓴다.
REFERENCE_NOTE = "아래 '참고'는 참고서 같은 정보다. 맞을 때만 쓰고, 문제 글·제한사항과 어긋나면 따르지 않는다. 판단의 근거는 문제 글이다."

ABSTRACT_SYSTEM = (
    "너는 코딩테스트 문제의 뼈대를 뽑는 분석자다. 문제 글의 이야기(사람, 물건, 장소)를 걷어 내고 풀이를 정하는 구조만 남긴다. "
    "이 결과는 사용자에게 보이지 않는다."
)


def abstract_text(problem_text: str) -> list[dict]:
    """뼈대 뽑기(abstract). 이야기가 달라도 구조가 같은 문제는 같은 명세가 나오게 정해진 낱말로 쓴다."""
    lines = [
        f"문제:\n{problem_text}",
        "spec: 이야기를 모두 걷어 낸 명세 2~3문장. 이 순서와 낱말로 쓴다 — "
        "입력(정수 배열/문자열 배열/문자열/2차원 배열/정수, 길이와 값의 범위, 중복 가능 여부) → 구하는 것(개수/최댓값/최솟값/참거짓/배열/남는 원소 하나 등) → "
        "핵심 조건(순서가 중요한가, 쌍을 고르는가, 연속인가, 뒤집을 수 있는가 등). 사람·물건·장소 이름과 변수 이름은 쓰지 않는다.",
        "patterns: 아래 목록에서 이 문제에 실제로 해당하는 단서의 id 1~2개(없으면 빈 배열). 제한사항의 입력 크기를 보고 고른다.",
        pattern_list(),
        "size: 제한사항에 적힌 입력 크기 가운데 가장 큰 값을 정수로(배열 길이, 문자열 길이 등. 없으면 0).",
        "skills: 아래 목록에서 이 문제를 코드로 옮길 때 꼭 필요한 구현 기술의 id 1~3개(없으면 빈 배열).",
        skill_list(""),  # 뼈대는 언어와 상관없이 문제마다 하나라 중립 말
        LEVEL_TEXT,
        "tags: 아래 기법 목록에서 이 문제의 풀이에 쓰는 방법의 id 2~4개(목록에 없는 낱말은 쓰지 않는다).",
        technique_list(""),
        'JSON {"spec", "patterns": [id], "size", "skills": [id], "level", "tags": [id]}',
    ]
    return [{"role": "system", "content": ABSTRACT_SYSTEM}, cached_user(lines, 1)]


# 단계 기준(1~5). 기본 문제 75개의 단계와 견주어 어긋남을 잰다
LEVEL_TEXT = ("level: 이 문제의 단계 1~5 하나(정수). 1: 한 가지 자료구조나 반복으로 푼다. 2: 기본 알고리즘 하나를 그대로 쓴다. "
              "3: 알고리즘 하나에 조건·상태 관리를 더한다. 4: 알고리즘 둘을 엮거나 상태 설계가 필요하다. 5: 최적화나 증명이 필요한 설계다.")

# 등록한 문제의 풀이를 실행으로 확인하는 두 호출. 둘 다 사용자에게 보이지 않는다
SHAPE = {
    "function": "solution 함수 하나로 쓴다(인자는 입출력 예와 같은 순서·형).",
    "program": "표준 입력을 읽어 표준 출력에 쓰는 프로그램으로 쓴다(입력·출력 형식 그대로).",
}
ONE_INPUT = {
    "function": "입력 하나는 solution에 넘길 인자들의 목록이다(입출력 예의 인자 순서·형 그대로). 예: [[1, 2, 3], 5]",
    "program": "입력 하나는 표준 입력에 넣을 글 전체다(입력 형식 그대로, 줄바꿈 포함). 예: \"3\\n1 2 3\\n\"",
}


def brute_messages(problem_text: str, mode: str) -> list[dict]:
    """단순 풀이: 정의를 그대로 옮긴 느린 풀이. 정답 풀이를 작은 입력에서 대조하는 데만 쓴다."""
    system = ("너는 코딩테스트 문제를 정의 그대로 푸는 검산자다. 빠르기는 상관없다. 틀릴 여지가 없는 가장 단순한 방법으로 푼다. "
              "이 코드는 다른 풀이를 작은 입력에서 대조하는 데만 쓰이고 사용자에게 보이지 않는다.")
    lines = [
        f"문제:\n{problem_text}",
        f"python 코드를 {SHAPE[mode]}",
        "모든 경우를 다 해 보거나 문제 글의 규칙을 한 줄씩 그대로 옮긴다. 정렬 뒤 고르기, 이분탐색, 점화식 같은 영리한 방법을 쓰지 않는다. "
        "작은 입력(길이 8 이하, 값 20 이하쯤)에서 1초 안에 끝나면 된다. 입력으로 받은 값을 바꾸지 않는다. 파일·네트워크·외부 모듈을 쓰지 않는다.",
        'JSON {"code"}',
    ]
    return [{"role": "system", "content": system}, cached_user(lines, 1)]


def maker_messages(problem_text: str, mode: str) -> list[dict]:
    """케이스 생성기: 작은 무작위·경계·함정·큰 입력을 만드는 파이썬 코드와, 생성된 입력을 앱이 규칙으로 검사할 제한사항."""
    system = "너는 코딩테스트 문제의 테스트 입력을 만드는 출제자다. 답은 쓰지 않고 입력만 만든다. 모든 입력은 문제의 제한사항을 지킨다."
    lines = [
        f"문제:\n{problem_text}",
        "python 코드 하나에 함수 small(), edge(), tricky(), large()를 쓴다. 저마다 입력의 목록을 돌려준다. 난수는 random 모듈만 쓰고 씨앗은 정하지 않는다(앱이 정한다). "
        "파일·네트워크·외부 모듈을 쓰지 않는다. 함수를 부르는 코드는 쓰지 않는다(앱이 붙인다).",
        ONE_INPUT[mode],
        "small(): 작은 무작위 입력 20~30개. 길이와 값을 작게(길이 1~8쯤) 잡아 모든 경우를 다 해 보는 풀이도 1초 안에 끝나게 한다.",
        "edge(): 경계 입력 5~15개. 제한사항에서 나오는 것: 가장 작은 입력, 같은 값만 있는 입력, 답이 없거나 0이 되는 입력, 값이 가장 크거나 작은 입력 등. 길이는 작게 둔다.",
        "tricky(): 함정 입력 3~10개. 흔한 실수를 하는 풀이가 틀리게 되는 입력이다: 범위의 끝에서 하나 차이로 틀리는 입력, 같은 값이 여러 번 나와 순서나 중복 처리가 갈리는 입력, "
        "0이나 음수가 섞여 부호를 놓치면 틀리는 입력, 결과가 32비트 정수를 넘는 입력, 눈앞의 최선을 고르면 틀리는 입력 등. 제한사항을 지키고 길이는 작게 둔다.",
        "large(): 효율성 입력 1~3개. 제한사항의 가장 큰 크기(길이·값)로 만들고, 느린 풀이(모든 쌍 보기 등)가 시간 안에 못 끝나는 모양으로 만든다. 입력 하나의 JSON이 2MB를 넘지 않게.",
        "bounds: 제한사항을 인자마다 적는다. arg는 몇 번째 인자(0부터. 표준 입출력은 0 하나에 입력 글의 모든 정수가 들 범위), "
        "low·high는 그 인자 안의 모든 정수의 가장 작은·큰 값, shortest·longest는 그 인자(배열·문자열)의 길이. 제한사항에 없는 것은 null.",
        'JSON {"code", "bounds": [{"arg", "low", "high", "shortest", "longest"}]}',
    ]
    return [{"role": "system", "content": system}, cached_user(lines, 1)]


HINT_RULES = [
    "- hints: 생각하는 의자가 그대로 쓰는 질문 3개. 0번은 이 블록이 왜 필요한지 묻는 열린 질문, 1번은 문제 글의 문장 하나를 작은따옴표로 그대로 인용해 가리키는 질문, 2번은 작은 예시 입력을 손으로 따라가게 하는 질문이다.",
    "- hints는 '예/아니요'로 답할 수 없는 질문이다('~가 필요할까요?'처럼 답을 넣어 놓고 맞는지 묻지 않는다). 무엇을·어떻게·왜를 묻는다.",
    "- 문제 글에 이미 적힌 것(주어진 값, 입력의 뜻, 구할 것)을 되묻거나 그것을 왜 알아야 하는지 묻지 않는다. 문제 글만 읽어서는 바로 나오지 않는 것(무엇을 기억해 둘지, 어떤 순서로 볼지, 언제 값을 바꿀지)을 묻는다.",
    "- 세 질문은 서로 다른 것을 묻는다(같은 문장을 되풀이하지 않는다). 0번도 이 블록이 맡은 일을 문제의 대상과 값으로 구체적으로 묻는다. 어느 블록에나 맞는 모호한 질문을 쓰지 않는다.",
    "- 인용은 문제 글의 문장을 줄이거나('…') 낱말 중간에서 끊지 않고 그대로 옮긴다. 문제 글에 없는 이름(참고 코드의 변수·인자 이름)을 쓰지 않는다.",
    "- 쉬운 말로 자연스럽게 쓴다. '예'·'아니요'·'참'·'거짓' 같은 판정 낱말을 명사처럼 써서('아니요에서 예로 바뀌는') 문장을 만들지 않고, 무엇이 어떻게 바뀌는지 풀어 쓴다.",
    f"- {OUTSIDE_PROBLEMS}",
    "- hints는 한국어 1–2문장이고 질문은 하나만 한다(물음표는 맨 끝에 한 번만). 정답 여부를 말하지 않는다. '맞아요', '좋아요', '정답', '잘했어요', '좋은 질문' 같은 말을 쓰지 않는다"
    "(구하는 값을 가리킬 때도 '정답' 대신 '답'이나 '결과'라고 쓴다). 코드, 코드 펜스, 다른 블록 이름을 쓰지 않는다.",
]


def draft_messages(state: MainState) -> list[dict]:
    ctx = state["ctx"]
    strategy = state.get("strategy") or "fresh"
    system = "\n".join(
        [
            "너는 코딩테스트 튜터의 블록 설계자다. 사용자가 직접 풀 수 있게 풀이를 사고 순서대로 블록으로 나눈다.",
            "원칙:",
            PRINCIPLES,
            "",
            GUIDE,
        ]
    )
    lines = [
        f"문제:\n{ctx.problem_text}",
        f"언어:{ctx.language}",
        "",
        "풀이 유형(algorithm)은 아래 15종 중 하나의 영문 키다. 허용 기법 안에서 푼다. 특별한 알고리즘 없이 문자열·규칙·계산을 조건대로 옮기면 되는 문제는 implementation, 상태가 단계마다 바뀌는 것을 따라가는 문제는 simulation이다.",
        SOLVE_SCOPE,
        "15종으로 풀 수 없는 문제면 가장 가까운 유형을 고르고 out_of_scope를 true로 한다.",
        METHOD_TEXT,
        "입력 크기 경험칙:",
        size_table(),
        "",
        "블록 종류(kind)는 이 다섯 가지만 쓴다.",
        KIND_TEXT,
        "",
        f"전략: {STRATEGY_TEXT[strategy]}",
    ]
    guide = solution_of(state)
    if guide is not None:
        lines += [
            "",
            "풀이 가이드(이 문제의 정답 풀이. 블록은 이 풀이를 위에서 아래로 나눈 것이다. 다른 풀이로 바꾸지 않는다):",
            *(["단서(문제 글의 어디에서 무엇을 읽는가. 블록의 hints 1번은 이 단서가 가리키는 문장을 인용해 묻는다):", *[f"- {clue}" for clue in guide.clues]] if guide.clues else []),
            f"방향: {guide.approach}",
            "단계:",
            *[f"- {step}" for step in guide.steps],
            f"코드(줄 번호 붙임):\n{numbered(guide.code)}",
        ]
    known = state.get("recall") or {}
    if known.get("patterns") or known.get("weak") or known.get("skills"):
        lines += ["", REFERENCE_NOTE]
    if known.get("patterns"):
        lines += ["참고 — 문제 글의 단서와 그것이 가리키는 기법:", *known["patterns"]]
    if known.get("skills"):
        lines += ["참고 — 코드로 옮길 때 필요한 구현 기술(해당 블록의 reference는 이 기술을 초보자가 읽기 쉬운 꼴로 쓴다):", *known["skills"]]
    if known.get("weak"):
        lines += ["참고 — 이 사용자가 여러 문제에서 되풀이한 실수(이 문제에 해당하는 블록이 있으면 그 블록의 checks와 hints에서 짚는다): " + ", ".join(known["weak"])]
    if strategy == "keep_flow":
        lines.append(f"사용자 코드:\n{ctx.direct_code}")
    if strategy == "follow":
        lines.append(f"사용자가 말한 방법:\n{state.get('follow') or ''}")
        now = ctx.plan
        if now is not None:
            lines.append("지금 계획의 흐름: " + " → ".join(f"{b.name}({b.goal})" for b in now.blocks))
            lines.append("사용자가 말한 방법이 지금 계획과 같은 방법이면(뒤 블록의 내용을 미리 말한 것 포함) 다시 짤 필요가 없다. followed를 false로 한다.")
    lines += [
        "",
        "블록마다 checks와 hints를 쓴다.",
        "- checks: 사용자가 이 블록을 찾았다고 볼 신호 1–3개. 말로 쓴다. 1번이 핵심이다.",
        *HINT_RULES,
        "",
    ]
    if guide is not None:
        lines += [
            "blocks는 풀이 가이드 코드의 줄을 1번 줄부터 마지막 줄까지 빠짐없이, 겹치지 않게, 순서대로 나눈 것이다. 블록 3~7개. 블록 하나는 한 가지 생각(단계 하나)이다.",
            "블록마다 lines에 [처음 줄 번호, 끝 줄 번호]를 적는다. 첫 블록은 1번 줄에서 시작하고, 다음 블록은 앞 블록의 끝 줄 바로 다음 줄에서 시작하고, 마지막 블록은 마지막 줄에서 끝난다.",
            "id는 b1부터 차례로, name은 짧은 이름, goal은 이 블록에서 정할 것 한 문장이다. reference는 쓰지 않는다(lines 구간이 그대로 참고 코드가 된다).",
            'JSON {"algorithm", "out_of_scope", "blocks": [{"id", "kind", "name", "goal", "lines": [처음, 끝], "checks", "hints"}]'
            + (', "followed": true 또는 false}' if strategy == "follow" else "}"),
            EXAMPLE_LINES,
        ]
    else:
        lines += [
            'blocks는 흐름 순서다. id는 b1부터 차례로, name은 짧은 이름, goal은 이 블록에서 정할 것 한 문장, '
            f"reference는 그 블록만의 짧은 {ctx.language} 참고 코드다.",
            'JSON {"algorithm", "out_of_scope", "blocks": [{"id", "kind", "name", "goal", "reference", "checks", "hints"}]'
            + (', "followed": true 또는 false}' if strategy == "follow" else "}"),
            example(ctx.language),
        ]
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}]


def hint_messages(state: MainState, blocks, faults: dict[str, list[str]], named: bool = False) -> list[dict]:
    """원칙을 어긴 블록의 질문만 다시 받는다. faults는 {블록 id: 어긴 원칙들}.
    named: 규칙으로 자른 블록이다. 블록마다 코드 구간을 보여 주고 이름·목표·신호·질문을 모두 받는다."""
    if named:
        rows = ["블록(흐름 순서. 코드는 이 블록이 맡은 정답 코드 구간이다):", *[f"- {b.id} ({b.kind}):\n{b.reference}" for b in blocks], "",
                "블록마다 name(짧은 이름), goal(이 블록에서 정할 것 한 문장), checks(사용자가 이 블록을 찾았다고 볼 신호 1–3개. 말로 쓴다. 1번이 핵심), hints를 쓴다."]
        shape = 'JSON {"blocks": [{"id", "name", "goal", "checks": ["..."], "hints": [질문 3개]}]}'
    else:
        rows = ["블록(흐름 순서):", *[f"- {b.id} {b.name}: {b.goal}" for b in blocks], "",
                "아래 블록의 hints가 규칙을 어겨 쓸 수 없다. 그 블록의 hints만 규칙에 맞게 다시 쓴다.",
                *[f"- {b.id}: 어긴 것 {', '.join(faults[b.id])}. 쓸 수 없는 hints: {json.dumps(b.hints, ensure_ascii=False)}" for b in blocks if b.id in faults]]
        shape = 'JSON {"blocks": [{"id", "hints": [질문 3개]}]}'
    lines = [f"문제 글:\n{state['ctx'].problem_text}", "", *rows, "", *HINT_RULES, shape]
    return [{"role": "system", "content": "너는 코딩테스트 튜터의 블록 설계자다. 생각하는 의자가 그대로 쓸 질문을 쓴다."}, {"role": "user", "content": "\n".join(lines)}]
