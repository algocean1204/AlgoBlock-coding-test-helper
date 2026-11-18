"""N3 블록 코드 판정. 출력이 [check]뿐이라 참고 코드를 비교 기준으로 넣어도 말풍선으로 새지 않는다.
차례: 이 자리의 표로 이름을 바꾼 계획 코드와 글자 그대로 같다(줄 끝 공백·빈 줄만 다름. 실행 없이 통과하는 유일한 길) → 실행 → 모델.
판정은 셋이다: 통과(Y) / 이어지지 않아요(N) / 확인 전(?). 앱이 아는 것은 '튜터의 코드와 이어지는가'뿐이라 판정이 그것만 말한다.
N(이어지지 않아요): 이어 돌린 실행이 끝까지 돌았는데 통과하지 못했다(어림 짝이면 시도할 짝을 모두 돌려 모두 실패했다. 오류가 누구 줄에서 났어도 같다).
말은 사실 → 두 가지 가능성(고칠 곳이 있다 / 튜터와 다른 방식이다) → 할 수 있는 일이다. 틀렸다고 하지 않는다.
확인 전: 결론까지 돌리지 못했다 — 이름·매개변수 차례를 찾지 못해 이어 붙이지 못함, 짝을 다 시도하지 못함(시간 한도), 모델이 읽고 거절함(실행하지 못함),
모델의 답이 형식에 맞지 않음. 틀린 수에 넣지 않는다.
불변 조건: 통과는 언제나 실행이 뒷받침한다. 블록을 잇는 일은 한 곳(spliced_view)에서 한다. 앞 블록이 바뀌면 뒤 블록의 통과를 물린다. 말은 한 일을 그대로 말한다.
실행: 이 블록은 방금 적은 코드, 사용자가 적어 통과한(또는 확인 전인) 다른 블록은 그 코드, 나머지는 계획 코드에 이름 바꾸기 표를 적용해 이은 프로그램을
채점 함수로 돌린다(효율성 케이스는 뺀다). 통과하지 못하면 내가 쓴 블록을 모두 이은 프로그램(튜터 코드 없이. 모아서 실행과 같은 글)을 한 번 더 돌려
숨은 테스트까지 통과하면 통과다.
뒤 블록이 쓰는 계획 이름을 사용자가 다른 이름으로 만들었으면 오류를 기다리지 않고 처음부터 짝지어 돌린다.
모델은 채점 함수가 없거나 채점하지 못했을 때(도구 없음, 케이스 없음)만 판정하고, 그 판정은 실행하지 못한 판단이라고 말한다.
풀이 가이드가 없거나 예시를 통과하지 못했으면(verified 거짓) 그 코드와 이어 돌린 결과로 판정하지 않는다."""

import difflib
import hashlib
import itertools
import json
import re
import time
from dataclasses import replace

import sys

from ..common.solution import (_TOKEN, body_lines, defined_function, frame_line, frame_of, guide_checked, made_statements, name_tables, open_braces, pairs_of,
                               unclosed_row,
                               scoped_names, solution_lines, solution_of, spliced, spliced_view, swap_names)
from ..common.talk_rules import (ALONE_LEAD, ALONE_OK, CANNOT_RUN, EXAMPLES_ONLY, MALFORMED, MANY_ANSWERS, SKIPPED, UNCHECKED_IN, UNRUN, UNRUN_FIX,
                                UNRUN_NO, UNVERIFIED, fence, unrun_why)
from .pairs import pair_block
from ..debug.rules import batchim, call_text
from ..llm import cached_user
from ..common.progress_view import active_plan, current_index, found_check
from ..save.respond import shown_count
from ..common.verdict import FOUND_RULE, ask_verdict
from ..state import BlockState, MainState, Verdict

USER_FAULT = ("failed", "timeout", "runtime_error", "compile_error")  # 사용자 코드 탓으로 끝난 채점
TRY_SECONDS = 6  # 첫 실행부터 이만큼 지나면 새 짝 시도를 시작하지 않는다(Python은 여러 번, 컴파일이 느린 언어는 한두 번 돈다)
now = time.monotonic  # 시험이 바꿔 끼우는 시계
# 없는 이름 오류: Python(뒤에서 대입하는 이름은 UnboundLocalError), Java, C++(gcc·clang), Rust, JavaScript
_MISSING = re.compile(r"NameError: name '(\w+)' is not defined|local variable '(\w+)'|symbol:\s+variable (\w+)"
                      r"|[‘'](\w+)[’'] was not declared|undeclared identifier '(\w+)'|cannot find value `(\w+)`"
                      r"|ReferenceError: (\w+) is not defined|Cannot access '(\w+)' before initialization")
# 없는 멤버·이름·클래스 오류의 원문은 다섯 언어 모두 쉬운 말로 알린다(이름은 위 _MISSING을 재사용한다)
_NO_MEMBER = re.compile(r"^cannot find symbol: (?!variable |class )\w+ (\w+)$|has no attribute '(\w+)'|no member named [‘'](\w+)[’']"
                        r"|no (?:method|field|function or associated item) named `(\w+)`|no field `(\w+)`|(\w+) is not a function")
_NO_CLASS = re.compile(r"^cannot find symbol: class (\w+)$|cannot find type `(\w+)` in this scope")
_NO_VAR = re.compile(r"^cannot find symbol: variable (\w+)$")
EASY_END = "확인해 보세요."
NO_MEMBER = "`{name}`{josa} 이름을 찾지 못했어요. 철자가 맞는지, 그 값에서 쓸 수 있는 이름인지 " + EASY_END
NO_NAME = "`{name}`{josa} 이름을 찾지 못했어요. 만들기 전에 썼거나 철자가 다른지 " + EASY_END
NO_CLASS = "`{name}`{josa} 이름을 찾지 못했어요. 맨 위의 가져오기(import)가 빠졌거나 철자가 다른지 " + EASY_END
# 실행 오류의 이유(다섯 언어의 같은 실수는 같은 뜻의 말로. 화면의 풀이와 뜻을 맞춘다). 앞에서부터 찾는다: map::at의 out_of_range는 '없는 키'가 먼저다
_RUNTIME = tuple((re.compile(pattern), said + EASY_END) for pattern, said in (
    (r"KeyError|no entry found for key|map::at|Map\.get\(", "없는 키를 읽었어요. 처음 보는 값일 때를 따져 보고, 읽기 전에 키가 있는지 "),
    (r"IndexError|IndexOutOfBounds|index out of bounds|out of range for slice|std::out_of_range(?!: sto)",
     "범위를 벗어난 자리를 읽었어요. 비어 있거나 마지막 자리 다음을 읽은 건 아닌지 "),
    (r"ZeroDivisionError|/ by zero|divide by zero|divisor of zero", "0으로 나눴어요. 나누는 값이 0이 되는 경우가 있는지 "),
    (r"RecursionError|StackOverflowError|Maximum call stack size exceeded|overflowed its stack|stack overflow",
     "재귀가 너무 깊어요. 끝나는 조건이 있는지, 반복문으로 바꿀 수 있는지 "),
    (r"NullPointerException", "null인 값을 썼어요. 만들지 않은 객체나 값이 없는 변수를 쓰기 전에 null인지 "),
    (r"Cannot read properties of (?:undefined|null)", "값이 없는(undefined, null) 걸 썼어요. 범위 밖 자리나 없는 키를 읽어 값이 없었는지 "),
    (r"sto\w+: out of range", "숫자가 너무 커서 그 형에 담지 못했어요. 바꾸는 글자의 크기를 "),
))
_MISMATCH = re.compile(r"incompatible types|possible lossy conversion|cannot convert|no viable conversion|invalid conversion from|mismatched types")
TYPE_MISMATCH = "값의 형이 맞지 않아요. 변수와 반환값의 형이 시작 코드와 같은지 " + EASY_END


def _easy(row: str) -> str:
    """없는 멤버·이름·클래스 오류, 흔한 실행 오류(_RUNTIME) 한 줄을 쉬운 말로. 아니면 빈 글."""
    for pattern, said in ((_NO_CLASS, NO_CLASS), (_NO_VAR, NO_NAME), (_NO_MEMBER, NO_MEMBER), (_MISSING, NO_NAME)):
        if found := pattern.search(row):
            name = next(g for g in found.groups() if g)
            return said.format(name=name, josa="이라는" if batchim(name) else "라는")
    return next((said for pattern, said in _RUNTIME if pattern.search(row)), "")


def compile_easy(text: str) -> str:
    """컴파일 오류 글의 첫 오류를 쉬운 말 한 줄로(없는 이름·멤버·클래스, 형이 맞지 않음). 흔하지 않은 오류는 빈 글."""
    row = _error_row(text, first=True, whole=True)  # 쉬운 말로 바뀐 줄이면 그대로(백틱이 '로 바뀌기 전에 _easy가 본다), 아니면 형 불일치만 본다
    return row if row.endswith(EASY_END) else TYPE_MISMATCH if _MISMATCH.search(row) else ""


SHOWN = 80  # 말에 싣는 값의 최대 길이(오류 원문은 자르지 않는다)
# 짝을 못 찾은 것을 '이 블록에서 만들어 주세요'(코드가 틀렸다는 말)로 말해, 그 말대로 하면 코드가 틀려지기도 했다. 짝을 못 찾았다는 사실과 할 수 있는 일을 말한다
HOLD_NAME = ("튜터가 채운 다음 블록 코드는 이 값을 {names}{josa} 이름으로 써요. 내 코드에서 어느 변수가 그 값인지 찾지 못해 이어 돌리지 못했어요. "
             "내 변수 이름을 그 이름으로 바꾸거나, 맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
# 이어 붙인 프로그램에 계획 코드로 이은 블록이 있으면 그 사실을 앞말로(내 코드가 틀렸다고 단정하지 않는다)
LEADS = {"later": "뒤 블록은 튜터의 코드로 채워서 돌리면", "earlier": "앞 블록은 튜터의 코드로 채워서 돌리면", "both": "다른 블록은 튜터의 코드로 채워서 돌리면"}
# 이어 돌린 실행이 끝까지 돌았는데 통과하지 못했다: 앱이 아는 것은 '튜터의 코드와 이어지지 않는다'뿐이다. 틀려서인지 다른 방식이어서인지는 모른다
NOT_JOINED = ("아직 고칠 곳이 있거나, 튜터와 다른 방식으로 써서 튜터의 코드와 맞물리지 않는 거예요. "
              "고치거나 튜터의 차례에 맞춰 써 보고, 맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
# 어림 짝을 쓴 실행: 어떻게 이었는지를 사실로 말한다. 시간이 모자라 다른 짝을 다 돌려 보지 못했으면 결론을 내지 못한 것이다(확인 전)
GUESSED = "튜터의 코드와 이을 때 같은 값으로 보고 이어 돌린 이름이에요(내 이름 → 튜터의 이름): {pairs}."
GUESSED_CUT = " 시간이 모자라 다른 짝은 다 돌려 보지 못해서 이어지지 않는 건지 확인하지 못했어요. 다르게 쓴 것이면 튜터의 이름으로 맞추거나 '이대로 넘어가기'를 눌러요."
# 'while'을 열고 증가를 다음 블록에 두려 하면 뒤 블록(계획 코드)에 증가가 없어 끝나지 않는다
WHILE_NOTE = "반복을 끝내는 줄(값을 늘리거나 줄이는 줄)을 뒤 블록에 두려 했다면 이 블록에 적어 주세요."
# 도우미 함수의 매개변수 차례를 바꾼 맞는 블록을 계획의 호출 차례가 만든 오류로 거부했다. 뒤 블록이 부르는 차례를 알린다
HOLD_PARAMS = ("튜터가 채운 다음 블록 코드는 이 블록의 함수를 {names} 차례로 넘겨 불러요. 내 함수의 매개변수가 그 차례의 어느 값인지 찾지 못해 이어 돌리지 못했어요. "
               "내 매개변수를 그 차례와 이름으로 바꾸거나, 맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
# 반복 안에서 시작해 밖에서 끝나는 블록을 평평하게 적으면 바깥 줄도 반복 안에 놓였다(Python만)
# 의자에서 이름이 아직 가려진 블록(찾기 전): 튜터 코드의 이름은 곧 찾을 답이라 위 세 말 대신 이름 없이 말한다
HOLD_HIDDEN = ("튜터가 채운 다음 블록 코드가 이 블록에서 받아 쓰는 값을 내 코드에서 찾지 못해 이어 돌리지 못했어요. "
               "이 블록을 찾으면 튜터가 쓰는 이름이 보여요. 맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
GUESSED_CUT_HIDDEN = ("튜터의 코드와 이을 이름의 짝을 시간 안에 다 돌려 보지 못해서 이어지지 않는 건지 확인하지 못했어요. "
                      "맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
INDENT_NOTE = "이 블록은 앞 블록에서 연 반복이나 조건 안에서 시작해요. 그 밖에서 할 일이 있으면 그 줄을 첫 줄보다 덜 들여 써 주세요."
KIND_WORD = {"compile_error": "컴파일 오류", "runtime_error": "실행 오류"}


def kept_code(raw: str) -> str:
    """저장·해시·비교하는 블록 코드: 맨 앞의 빈 줄과 끝 공백만 뗀다. 첫 줄의 들여쓰기는 바깥으로 나가는 줄을 가늠하는 기준이라 남긴다."""
    return re.sub(r"^\s*\n", "", (raw or "").rstrip())


def code_hash(code: str) -> str:
    return hashlib.sha256(kept_code(code).encode("utf-8")).hexdigest()


def hold_name(names: list[str], params: bool = False, hide: bool = False) -> str:
    """hide: 의자에서 이름이 아직 가려진 블록이다(이름을 싣지 않는다)."""
    if hide:
        return HOLD_HIDDEN
    names = list(dict.fromkeys(names))
    return (HOLD_PARAMS if params else HOLD_NAME).format(names=", ".join(f"`{name}`" for name in names), josa="이라는" if names and batchim(names[-1]) else "라는")


def assumed(pairs: list[list[str]], cut: bool = False, hide: bool = False) -> str:
    """어림 짝 문장. pairs: [[내 이름, 계획 이름], …]. 같은 이름끼리의 짝은 말하지 않는다. cut: 다른 짝을 다 시도하지 못했다(짝 말이 비어도 그 사실은 말한다).
    둘 다 없으면 빈 글. hide: 의자에서 이름이 아직 가려진 블록이다(짝을 말하지 않고, 다 시도하지 못했으면 그 사실만)."""
    if hide:
        return GUESSED_CUT_HIDDEN if cut else ""
    shown = [f"`{m}` → `{p}`" for m, p in pairs if m != p]
    return ((GUESSED.format(pairs=", ".join(shown)) if shown else "") + (GUESSED_CUT if cut else "")).strip()


def examples_only(report: dict) -> bool:
    """채점이 숨은 테스트 없이 공개 예시로만 돌았다(통과가 약하다)."""
    cases = report.get("cases") or []
    return bool(cases) and all(case.get("kind") == "example" for case in cases)


def program_of(state: MainState) -> bool:
    """문항이 표준 입출력(프로그램) 방식인가. 서버가 아는 문항의 방식을 받는다(코드 모양으로 짐작하지 않는다)."""
    return state["ctx"].mode == "program"


def unrun_note(why: str) -> str:
    """실행하지 못해 코드를 읽고 본 통과의 말. why: 채점하지 못한 까닭(채점 결과의 status)."""
    return UNRUN.format(why=unrun_why(why)) + UNRUN_FIX.get(why, "")


def guide_gap(state: MainState, check) -> dict | None:
    """풀이 가이드를 믿을 수 없어 이 블록을 계획 코드와 이어 돌려 판정할 수 없을 때의 결과(run_verdict와 같은 꼴). 믿을 수 있으면 None.
    가이드가 없거나 예시를 통과하지 못했다: 판정하지 않고 '확인 전'으로 넘긴다. 채점하지 못해 확인하지 못했다(도구·케이스가 없음): 이 블록도 같은 까닭으로
    돌리지 못하므로 그 까닭을 들어 '실행하지 못함'으로 보낸다. 그 사이 도구를 설치해 가이드가 지금은 통과하면 믿고 이어 돌린다(저장된 값은 그대로다).
    지금은 통과하지 못하면 예시를 통과하지 못한 가이드와 같다."""
    guide = solution_of(state)
    if guide is not None and guide.verified:
        return None
    if guide is not None and guide.verified is None:
        status = "" if check is None else (check(state["ctx"].problem_id, guide.code, quick=True) or {}).get("status") or "no_cases"
        if status == "passed":
            return None
        if status not in USER_FAULT:
            return {"unrun": status}
    return {"verdict": Verdict(True, seen=UNVERIFIED, hint=False, ran=False), "stored": [], "told": [], "fixes": []}


def saved_states(state: MainState) -> dict[str, BlockState]:
    """이번 요청에서 계획을 새로 만들었으면 예전 블록 판정은 쓰지 않는다."""
    return {} if state.get("plan") is not None else state["ctx"].block_states


KEPT = ("Y", "?")  # 저장된 글을 이어 붙이는 블록: 통과했거나, 확인 전으로 남은 블록(앞 블록이 바뀌었다, 실행하지 못하고 통과했다, 이대로 넘어갔다)


def passed_pairs(state: MainState, plan, skip: int | None = None) -> dict[int, dict[str, str]]:
    """사용자가 통과시킨(또는 확인 전으로 돌아간) 블록(skip은 뺀다)이 내놓는 이름 짝 {블록 순번: {계획 이름: 내 이름}}.
    name_tables(tables_of)로 블록 자리마다의 표를 만든다(블록 코드 확인·채우기가 같이 쓴다)."""
    states, language, program = saved_states(state), state["ctx"].language, program_of(state)
    return {i: pairs_of(b.reference, states[b.id].code, states[b.id].renames, language, program)
            for i, b in enumerate(plan.blocks) if i != skip and b.id in states and states[b.id].verdict in KEPT}


def tables_of(state: MainState, plan, pairs: dict) -> list[dict]:
    """블록 자리마다의 이름 바꾸기 표. 도우미 함수 안에서만 사는 이름의 짝은 그 함수가 끝나면 뺀다."""
    refs, language = [b.reference for b in plan.blocks], state["ctx"].language
    return name_tables(len(refs), pairs, scoped_names(refs, language, program_of(state)))


def code_messages(state: MainState, plan, index: int, code: str) -> list[dict]:
    block = plan.blocks[index]
    states = saved_states(state)
    # 앞 블록은 확인받은 코드, 없으면(채우기로 연 블록) 계획의 코드
    before = [f"# {b.name}\n{states[b.id].code if b.id in states else b.reference}" for b in plan.blocks[:index]]
    checks = [f"{n}. {text}" for n, text in enumerate(block.checks, 1)] or ["없음(목표로 판단)"]
    system = "너는 코딩테스트 튜터의 판정자다. 사용자가 쓴 블록 코드 하나가 그 블록의 목표를 해내는지만 본다."
    guide = solution_lines(state)
    lines = [
        f"문제:\n{state['ctx'].problem_text}",
        f"언어:{state['ctx'].language}",
        *guide,
        f"이 블록:{block.name} ({block.kind})",
        f"목표:{block.goal}",
        "신호:",
        *checks,
        f"참고 코드(비교용. 같을 필요 없다):\n{block.reference}",
        "앞 블록 코드:\n" + ("\n".join(before) or "없음"),
        "판단 기준: 사용자 블록 코드가 참고 코드와 같은 일을 하면(변수 이름이나 쓰는 꼴만 다르면) Y다. "
        "다르면 신호를 1번부터 하나씩 보고, 사용자 블록 코드가 그 신호를 해내는지 본다. 모두 해내면 Y, 못 해낸 신호가 있으면 N과 그 첫 신호 번호다. "
        "같은 일을 다른 식으로 쓴 것은 해낸 것이다. 참고 코드도 이 블록만으로는 드러내지 않는 신호(뒤 블록에서 이루어지는 것)는 따지지 않는다. "
        "실행은 하지 않는다. 문법이 조금 틀려도 의도가 맞으면 해낸 것이다.",
        f"사용자 블록 코드:\n{code}",
    ]
    return [{"role": "system", "content": system}, cached_user(lines, 2 + len(guide))]


def missing_name(report: dict) -> str:
    """채점 결과의 없는 이름 오류에서 그 이름. 없으면 빈 글."""
    text = "\n".join([report.get("compile") or "", *((case.get("error") or "") for case in report.get("cases") or [])])
    found = _MISSING.search(text)
    return next(group for group in found.groups() if group) if found else ""


def _cut(text) -> str:
    """한 줄로 펴고 SHOWN자를 넘으면 낱말 경계에서 자른다(공백이 없으면 글자에서)."""
    text = " ".join(str(text if text is not None else "").split()).replace("`", "'")
    if len(text) <= SHOWN:
        return text
    head = text[:SHOWN + 1]
    return (head[:head.rfind(" ")] if " " in head else text[:SHOWN]) + "…"


def _error_row(text: str, first: bool = False, whole: bool = False, easy: bool = True) -> str:
    """오류 글에서 한 줄: 오류 이름이 있는 줄(컴파일 오류는 첫 줄, 실행 오류는 마지막 줄). 임시 폴더 경로는 뗀다.
    모은 파일의 '파일이름:줄(:칸): error: '는 사용자가 볼 수 없어 떼고, Java 'cannot find symbol'에는 그 이름을 붙이고,
    Python의 'Did you mean: …' 꼬리(고칠 답)는 뗀다. whole이면 자르지 않는다."""
    if not first:  # 실행 오류의 이유 줄을 고른다: Rust 패닉의 머리는 떼어 이유 줄이 남게 하고, 안내(note:)와 스택 줄(at …)은 건너뛴다
        text = re.sub(r"thread '[^']*'(?: \(\d+\))? panicked at [^\n]*?\d+:\d+:\n", "", text or "")
        text = re.sub(r"thread '[^']*'(?: \(\d+\))? panicked at '(.*)', \S+:\d+:\d+", r"\1", text)
    rows = [re.sub(r"[^\s\"'`]+[/\\]", "", row).strip() for row in (text or "").splitlines() if row.strip()]
    rows = rows if first else [row for row in rows if not re.match(r"(?:note|help):|stack backtrace|at |\d+: ", row)]
    named = [i for i, row in enumerate(rows) if re.search(r"error|exception", row, re.IGNORECASE)] or list(range(len(rows)))
    if not named:
        return ""
    at = named[0] if first else named[-1]
    row = re.sub(r"^[\w.-]+:\d+(?::\d+)?:\s*", "", rows[at])
    row = re.sub(r"^(?:fatal\s+)?error(?:\[\w+\])?:\s*", "", row)
    row = re.sub(r"^Exception in thread \"[^\"]*\" ", "", row)  # Java: 머리와 패키지 이름은 떼고 예외 이름과 메시지만
    row = re.sub(r"\b(?:[a-z_]\w*\.)+(?=[A-Z]\w*(?:Error|Exception)\b)", "", row)
    if row.startswith("cannot find symbol"):
        symbol = next((f"{m.group(1)} {m.group(2)}" for later in rows[at + 1:] if (m := re.search(r"symbol:\s+(\w+)\s+(\w+)", later))), "")
        row = f"cannot find symbol: {symbol}" if symbol else row
    row = re.sub(r"\.? Did you mean: .*$", "", row)
    row = re.sub(r"[ ,]*(?:on |at )?\(?\bline \d+\)?", "", row)  # 이어 붙인 프로그램의 줄 번호는 사용자가 볼 수 없다(난 곳은 따로 말한다. 'deadline 5'는 낱말이다)
    if easy and (said := _easy(row)):
        return said
    return " ".join(row.split()).replace("`", "'") if whole else _cut(row)


def _same_form(got) -> str:
    """나온 값이 JSON으로 읽히면 기대한 값과 같은 꼴로 다시 적는다(C++ 러너의 '[1,0,0]'과 기대한 값 '[3, 2, 0]')."""
    try:
        return json.dumps(json.loads(got), ensure_ascii=False)
    except (TypeError, ValueError):
        return "" if got is None else str(got)


def _said(line: str, lead: str = "") -> str:
    """오류 한 줄을 말로: 채점 결과의 한도 말처럼 문장이면 그대로, 아니면 '`…`가 났어요.'(앞말이 있으면 '…가 나요.')."""
    if re.search(r"(습니다|어요|에요|요)\)?\.?$", line):
        return line if line.endswith(".") else line + "."
    return f"`{line}`{_ga(line)} {'나요' if lead else '났어요'}."


def _ga(text: str) -> str:
    """오류 글·값 뒤의 조사. 따옴표·마침표로 끝나면 '가'(''NoneType'가', ''max'.가')."""
    if re.search(r"['\".]$", text.strip()):
        return "가"
    return "이" if batchim(text) else "가"


def seen_line(report: dict, program: bool, lead: str = "") -> str:
    """통과하지 못한 채점에서 본 것 한 줄. 공개 예시(kind example)에서 틀렸을 때만 입력과 값을 말한다. kind가 없으면 숨은 케이스로 본다.
    lead: 앞말(계획 코드로 이은 블록이 있다). 있으면 '…돌리면 …나와요'처럼 지금 말로 붙인다."""
    said = _seen(report, program, lead)
    return f"{lead} {said}" if lead else said


def _seen(report: dict, program: bool, lead: str) -> str:
    def now_(present: str, past: str) -> str:  # 앞말이 있으면 '나와요', 없으면 '나왔어요'
        return present if lead else past

    bad = [case for case in report.get("cases") or [] if case.get("status") != "passed"]
    case = next((c for c in bad if c.get("kind") == "example"), bad[0] if bad else None)
    if case is None:  # 컴파일 오류처럼 케이스 없이 끝났다
        line = _error_row(report.get("compile") or "", first=True, whole=True)
        return _said(line, lead) if line else now_("실행하지 못해요.", "실행하지 못했어요.")
    shown = case.get("kind") == "example"
    if case.get("status") == "timeout":
        return now_("끝나지 않거나 너무 오래 걸려요.", "끝나지 않거나 너무 오래 걸렸어요.")
    if case.get("status") == "failed":
        if not shown:
            return now_("예시는 맞지만 숨은 테스트에서 틀려요.", "예시는 맞지만 숨은 테스트에서 틀렸어요.")
        got = _cut(_same_form(case.get("got")))
        if program:  # 어느 예시인지, 무엇이 나왔는지 말한다(화면이 부르는 '예시 1'과 맞춘다)
            n = [c for c in report.get("cases") or [] if c.get("kind") == "example"].index(case) + 1
            if "\n" in str(case.get("expected") or "").strip("\n") or "\n" in str(case.get("got") or "").strip("\n"):  # 여러 줄 출력은 줄을 지킨 글상자로
                return (f"예시 {n}의 출력이 기대와 달라요.\n기대한 출력:\n{fence(case.get('expected'))}\n"
                        f"{now_('내 출력', '나온 출력')}:\n{fence(case.get('got')) if str(case.get('got') or '').strip() else '(아무것도 나오지 않았어요)'}")
            head = f"예시 {n}의 기대한 출력은 {_cut(case.get('expected'))}인데"
        else:
            head = f"예시 `{_cut(call_text(case.get('input', '')))}`의 기대한 값은 {_cut(case.get('expected'))}인데"
        return (f"{head} {got}{_ga(got)} {now_('나와요', '나왔어요')}." if got
                else f"{head} 아무것도 {now_('나오지 않아요', '나오지 않았어요')}.")
    line = _error_row(case.get("error") or report.get("compile") or "", whole=True, easy=shown)  # 숨은 테스트는 이름만 말한다(쉬운 말에는 내 코드의 이름이 든다)
    if not shown:  # 숨은 테스트의 오류는 이름만
        name = (re.findall(r"[A-Za-z_]\w*(?:Error|Exception)", line) or [""])[-1]
        if re.search(r"(습니다|어요|에요|요)\.?$", line):
            return "숨은 테스트에서 " + _said(line, lead)
        return (f"숨은 테스트에서 `{name}`{_ga(name)} {now_('나요', '났어요')}." if name
                else f"숨은 테스트에서 실행 오류가 {now_('나요', '났어요')}.")
    return _said(line, lead) if line else f"실행 오류가 {now_('나요', '났어요')}."


def _pairings(open_names: list[str], candidates: dict[str, list[str]], taken: set[str]):
    """후보가 있는 이름들에 후보를 겹치지 않게 나눠 주는 모든 경우(후보 차례대로. 짝 없이 두는 것은 맨 뒤)."""
    lists = [[c for c in candidates[name] if c not in taken] + [None] for name in open_names]
    for combo in itertools.product(*lists):
        picked = [c for c in combo if c]
        if len(picked) == len(set(picked)):
            yield {name: c for name, c in zip(open_names, combo) if c}


def _early(states: dict, plan, index: int, skip: int, language: str, program: bool) -> list:
    """블록 index 앞의 내 블록(통과했거나 확인 전)에서 내가 만들었고 아직 어느 계획 이름과도 짝이 없는 이름의 만드는 문장(
    계획보다 한 블록 먼저 만든 변수). 계획에 있는 이름, 저장된 짝의 내 이름, 반복 변수·매개변수, 내 블록 어디서든 다시 나오는 이름은 뺀다."""
    words = set(re.findall(r"[A-Za-z_]\w*", "\n".join(b.reference for b in plan.blocks)))
    own = plan.blocks[index].id  # 이 블록이 지난번에 지은 짝은 다시 짓는 중이라 뺀다(앞 블록 무리를 다시 읽을 때)
    paired = {mine for key, item in states.items() if key != own for mine, _ in item.renames}
    counts = {}
    for i, b in enumerate(plan.blocks):
        if i != skip and b.id in states:
            for tok in _TOKEN.findall("\n".join(body_lines(states[b.id].code, language, program))):
                counts[tok] = counts.get(tok, 0) + 1
    out = []
    for b in plan.blocks[:index]:
        saved = states.get(b.id)
        if saved is not None and saved.verdict in KEPT:
            out += [item for item in made_statements(saved.code, language, program)
                    if item[1] not in ("loop", "param") and item[0] not in words and item[0] not in paired and counts.get(item[0], 0) <= 1]
    return out


def _analysis(state: MainState, plan, index: int, code: str, tables: list[dict]):
    """이 블록의 짝(pairs.pair_block)과 앞 블록(통과한 사용자 블록)의 바꿔도 되는 무리 [(블록 순번, 계획 이름들, 지금 차례의 내 이름들)]."""
    refs, language, program = [b.reference for b in plan.blocks], state["ctx"].language, program_of(state)
    made = [{n for n, *_ in made_statements(ref, language, program)} for ref in refs]
    scopes = scoped_names(refs, language, program)
    # 앞 블록의 계획이 만든 이름. 끝난 도우미 함수 안에서만 산 이름은 빼고 본다(예: solution의 left는 도우미 매개변수 left와 다른 새 이름이다)
    earlier = lambda j: set().union(*made[:j]) - {n for end, names in scopes if end < j for n in names} if j else set()  # noqa: E731
    states, loose = saved_states(state), []
    for j, block in enumerate(plan.blocks[:index]):
        saved = states.get(block.id)
        if saved is None or saved.verdict not in KEPT:
            continue
        stored = {plan_name: mine for mine, plan_name in saved.renames}
        groups = pair_block(refs[j], saved.code, tables[j], "\n".join(refs[j + 1:]), earlier(j), language, program, [g[1:] for g in loose],
                            _early(states, plan, j, index, language, program)).groups
        for plans, mine in groups:
            order = [stored.get(p, p) for p in plans]
            ended = {n for end, names in scopes if j <= end < index for n in names}  # 이미 끝난 도우미 안에서 지은 무리는 이 블록 뒤에 쓰이지 않는다
            if sorted(order) == sorted(mine) and len(plans) > 1 and not set(plans) & ended:
                loose.append((j, plans, order))
    info = pair_block(refs[index], code, tables[index], "\n".join(refs[index + 1:]), earlier(index), language, program, [g[1:] for g in loose],
                      _early(states, plan, index, index, language, program))
    return info, loose


def _aligned(reference: str, code: str, table: dict, loose: list, language: str, program: bool) -> list:
    """이 블록의 계획 코드와 내 코드를 낱말 줄로 맞대어, 앞 블록의 굳지 않은 무리가 어느 차례여야 하는지 읽는다([(블록 순번, 계획 이름들, 차례)]).
    'drop_old(low, left)' ↔ 'my_drop_old(my_low, my_left)'처럼 같은 자리에 오는 이름끼리 짝이다. 무리마다 하나씩 맞물릴 때만."""
    plan_loose = {p: gi for gi, (_, plans, _) in enumerate(loose) for p in plans}
    mine_loose = {m: gi for gi, (_, _, order) in enumerate(loose) for m in order}
    tok = lambda text: [t for line in body_lines(text, language, program) for t in _TOKEN.findall(line)]  # noqa: E731
    plan_toks, mine_toks = tok(reference), tok(code)
    a = ["?" if t in plan_loose else table.get(t, t) for t in plan_toks]
    b = ["?" if t in mine_loose else t for t in mine_toks]
    votes = {}
    for i, j, n in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(n):
            p, m = plan_toks[i + k], mine_toks[j + k]
            if p in plan_loose and plan_loose[p] == mine_loose.get(m):
                votes.setdefault(p, {}).setdefault(m, 0)
                votes[p][m] += 1
    out = []
    for gi, (j, plans, order) in enumerate(loose):
        pick = [max(votes[p], key=votes[p].get) if p in votes else None for p in plans]
        rest = iter([m for m in order if m not in pick])  # 이 블록에 나오지 않는 이름은 남은 이름을 차례대로
        pick = [m if m is not None else next(rest, None) for m in pick]
        if None not in pick and sorted(pick) == sorted(order) and pick != order:
            out.append((j, plans, pick))
    return out


def _recreated(name: str, later: list[str], language: str, program: bool) -> bool:
    """뒤 블록이 그 이름을 읽기 전에 스스로 새로 만든다(반복 변수 등). HOLD_NAME 목록에 넣지 않는다."""
    for ref in later:
        toks = [t for line in body_lines(ref, language, program) for t in _TOKEN.findall(line)]
        if name not in toks:
            continue
        made = {n: kind for n, kind, *_ in made_statements(ref, language, program)}
        at = toks.index(name)
        return made.get(name) == "loop" or (name in made and toks[at + 1:at + 2] in (["="], [":="], [","]))
    return False


def name_hidden(state: MainState, index: int) -> bool:
    """의자에서 이름이 아직 가려진 블록(말로 찾거나 끝내기 전)을 확인한다: 확인 말에 튜터 코드의 이름을 싣지 않는다. 가이드는 언제나 False."""
    return state["request"].mode == "chair" and index >= shown_count(state["ctx"], "chair")


def run_verdict(state: MainState, plan, index: int, code: str, check) -> dict | None:
    """실행 판정. 모델에 넘길 때는 None. 돌려주는 것: verdict, stored(저장할 짝 [[내 이름, 계획 이름], …]), told(알릴 굳은 짝), fixes(다시 고른 앞 블록 상태).
    이어 붙이는 것은 지금 화면의 글 그대로다 — 저장된 블록(적었거나 채운 블록, 앞이든 뒤든)은 저장된 글, 지금 블록은 넣은 글, 나머지는 계획 코드(표로 이름을 바꿈).
    첫 가정(굳은 짝 + 무리는 나온 차례 + 첫 후보)으로 돌리고, 통과하지 못하면 이 블록의 다른 후보·무리의 다른 차례, 앞 블록의 굳지 않은 무리의 다른 차례를
    시간 한도 안에서 돌린다. 그래도 통과하지 못하면 내가 쓴 블록을 모두 이은 프로그램을 한 번 돌려, 숨은 테스트까지 통과하면 통과다(alone).
    통과하지 못하면 첫 가정의 결과로 말한다(failure_verdict): 짝을 다 시도했으면 '이어지지 않아요'(N), 시간 한도로 다 시도하지 못했으면 '확인 전'(unsure).
    실행하지 못하면 {"unrun": 까닭(채점 결과의 status, 모르면 빈 글)}(모델이 판정한다)."""
    refs = [b.reference for b in plan.blocks]
    if check is None or not code.strip() or not all(ref.strip() for ref in refs):
        return {"unrun": ""}
    ctx, language, program = state["ctx"], state["ctx"].language, program_of(state)
    states = saved_states(state)
    # 통과했거나 확인 전(?)인 블록은 저장된 글 그대로(뒤 블록도). 마지막 확인이 통과하지 못한(N) 블록은 계획 코드(이 자리의 표)로 잇는다
    # (그러지 않으면 넘어가지 못한 뒤 블록의 글 탓에 맞게 고친 앞 블록이 '이어지지 않아요'가 된다)
    mine = {i: states[b.id].code for i, b in enumerate(plan.blocks) if i != index and b.id in states and states[b.id].verdict in KEPT}
    plan_blocks = [i for i in range(len(refs)) if i != index and i not in mine]  # 계획 코드로 잇는 블록
    written = {i: states[b.id].code for i, b in enumerate(plan.blocks) if i != index and b.id in states and states[b.id].code.strip()}  # 내가 쓴 블록 모두

    def alone() -> dict | None:
        """내가 쓴 블록을 모두(마지막 확인이 통과가 아닌 것도) 이은 프로그램(튜터 코드 없이. 모아서 실행과 같은 글)이 통과하면 통과 결과.
        앞 블록 가운데 글이 없는 것이 있거나, 숨은 테스트 없이 공개 예시로만 돌았으면 이 길로 통과시키지 않는다. 그때까지 확인 전이던 내 블록도 통과로 바꾼다.
        통과가 아닌 블록의 글을 빼고 돌려 '지금까지 쓴 코드만으로 통과해요'라 했는데 그 글로 모으면 오류였다."""
        if any(i not in written for i in range(index)):
            return None
        report = check(ctx.problem_id, spliced(refs, index, code, language, written, None, program, ctx.starter, own_only=True), quick=True) or {}
        if report.get("status") != "passed" or examples_only(report):
            return None
        return {"verdict": Verdict(True, seen=ALONE_OK), "stored": [], "told": [], "fixes": list(promote(written).values())}

    def promote(blocks: dict) -> dict[int, BlockState]:
        return {i: replace(item, verdict="Y") for i in blocks if (item := states.get(plan.blocks[i].id)) is not None and item.verdict == "?"}

    if plan_blocks and (gap := guide_gap(state, check)):  # 가이드를 믿을 수 없다: 그 풀이와 이어 돌린 결과는 내 블록의 판정이 될 수 없다
        return alone() or gap
    pairs = passed_pairs(state, plan, skip=index)
    base = tables_of(state, plan, pairs)
    info, loose = _analysis(state, plan, index, code, base)
    plan_fn, my_fn = defined_function(refs[index], language, program), defined_function(code, language, program)
    fn = {plan_fn: my_fn} if plan_fn and my_fn and plan_fn != my_fn else {}  # 도우미 함수 이름만 바꿨다
    first = info.guess()
    words, typed = set(re.findall(r"[A-Za-z_]\w*", "\n".join(refs))), set(re.findall(r"[A-Za-z_]\w*", code))
    plan_words = set(re.findall(r"[A-Za-z_]\w*", "\n".join(refs[i] for i in plan_blocks)))
    used = [g for g in loose if set(g[1]) & plan_words]  # 이 실행에 쓰이는 앞 블록의 굳지 않은 짝
    aligned = _aligned(refs[index], code, base[index], used, language, program)

    def but(trial, again):  # 앞 블록 무리의 차례를 바꾸면 그 계획 이름은 그 차례가 정한다(이 블록의 어림 짝은 버린다)
        names = {p for _, plans, _ in again for p in plans}
        return {k: v for k, v in trial.items() if k not in names}

    def trials():
        if aligned:  # 내 코드가 앞 블록의 이름을 쓰는 자리로 고른 차례를 먼저(그 차례로 통과하면 앞 블록의 짝을 고쳐 쓴다)
            yield but(first, aligned), tuple(aligned)
        yield first, ()
        settled = {k: v for k, v in first.items() if k not in info.candidates}
        for alt in _pairings(list(info.candidates), info.candidates, set(info.fixed.values()) | {m for _, ms in info.groups for m in ms}):
            yield {**settled, **alt}, ()
        for plans, order in info.groups:
            for perm in itertools.permutations(order):
                yield {**first, **dict(zip(plans, perm))}, ()
        for j, plans, order in used:
            for perm in itertools.permutations(order):
                if list(perm) != order:
                    yield but(first, [(j, plans, perm)]), ((j, plans, list(perm)),)
        if len(used) > 1:  # 여러 무리를 함께 바꾸는 차례
            for perms in itertools.product(*[list(itertools.permutations(order)) for _, _, order in used]):
                again = tuple((j, plans, list(perm)) for (j, plans, _), perm in zip(used, perms))
                yield but(first, again), again

    reports, tried, started, last, cut = [], [], now(), 0.0, False  # cut: 짝을 다 시도하지 못했다(시간 한도, 끝나지 않는 반복)
    for trial, again in trials():
        if (trial, again) in tried:
            continue
        if reports and now() - started + last > TRY_SECONDS:  # 이번 시도가 한도를 넘겨 끝날 것 같으면 시작하지 않는다
            cut = True
            break
        tried.append((trial, again))
        table = {**but(info.own, again), **fn, **trial}  # 그대로 쓴 이름도 앞 블록 무리의 바꾼 차례를 덮지 않는다
        changed = {}
        for j, plans, perm in again:
            changed[j] = {**changed.get(j, pairs.get(j, {})), **dict(zip(plans, perm))}
        tables = tables_of(state, plan, {**pairs, **changed, index: table})
        begun = now()
        text, spans = spliced_view(refs, index, code, language, mine, tables, program, ctx.starter)
        report = check(ctx.problem_id, text, quick=True) or {}
        last = now() - begun
        if report.get("status") == "entry_missing":  # 이어 붙이기의 잘못이다(사용자 탓이 아니다)
            print(f"[code_check] 진입 함수가 없는 실행: {ctx.problem_id} 블록 {index + 1}", file=sys.stderr)
            return {"verdict": Verdict(False, seen=CANNOT_RUN, hint=False, unsure=True), "stored": [], "told": [], "fixes": []}
        if not reports and report.get("status") not in ("passed", *USER_FAULT):
            return {"unrun": report.get("status") or "no_cases"}  # 채점하지 못했다(도구 없음, 다루지 못하는 인자 형, 케이스 없음)
        reports.append((report, trial, again, tables, spans))
        if report.get("status") == "passed":
            fixes = {}
            for j, plans, perm in again:  # 앞 블록의 저장된 짝을 새 차례로 고쳐 쓴다
                saved = fixes.get(j) or states[plan.blocks[j].id]
                kept = [pair for pair in saved.renames if pair[1] not in plans]
                fixes[j] = BlockState(saved.block_id, saved.code, saved.code_hash, saved.verdict, saved.miss, saved.tries,
                                      kept + [[m, p] for p, m in zip(plans, perm) if m != p])
            keep = set(info.open) | set(fn)  # 뒤 블록이 읽는 이름의 짝만 남긴다
            stored = [[m, p] for p, m in {**fn, **trial}.items() if m != p and p in keep]
            told = [[m, p] for p, m in {**fn, **info.fixed}.items() if p in keep and m != p and (trial.get(p) == m or p in fn)]
            weak = examples_only(report)
            said = any(EXAMPLES_ONLY in m.text for m in (*ctx.chair, *ctx.guide))  # 그 문제에서 처음 한 번만 말한다(배지는 화면이 따로 보인다)
            if not plan_blocks and not weak:  # 튜터의 코드 없이 내 블록만으로 통과했다: 확인 전이던 내 블록도 통과다(공개 예시로만 돌았으면 올리지 않는다)
                for i, item in promote(mine).items():
                    fixes[i] = replace(fixes[i], verdict="Y") if i in fixes else item
            return {"verdict": Verdict(True, seen=EXAMPLES_ONLY if weak and not said else ""), "stored": stored, "told": told, "fixes": list(fixes.values())}
        if report.get("status") == "timeout":
            cut = any(item not in tried for item in trials())
            break  # 끝나지 않는 반복: 다른 짝으로 다시 기다리지 않는다
    if plan_blocks and (found := alone()):
        return found
    told, trial, again, tables, spans = reports[0]
    missing = missing_name(told)
    later = [i for i in plan_blocks if i > index]
    lead = LEADS["both" if later and len(later) < len(plan_blocks) else "later" if later else "earlier"] if plan_blocks else ""
    # 그 실행에서 계획 코드에 쓴 굳지 않은 짝(이 블록의 무리·후보, 앞 블록의 무리). 계획 코드에 그 이름이 나올 때만. 같은 이름끼리의 짝은 어림이 아니다
    moved = {(j, tuple(plans)): perm for j, plans, perm in again}
    guessed = {p: m for p, m in {**{p: trial[p] for plans, _ in info.groups for p in plans if p in trial},
                                 **{p: trial[p] for p in info.candidates if p in trial},
                                 **{p: m for j, plans, order in used for p, m in zip(plans, moved.get((j, tuple(plans)), order))}}.items()
               if p in plan_words and p != m}
    # 뒤 블록이 읽는데 그 실행의 표에 짝이 없고(앞 블록의 짝도 없다) 뒤 블록이 스스로 만들지도 않는 이름
    later_words = set(re.findall(r"[A-Za-z_]\w*", "\n".join(refs[i] for i in later)))
    no_pair = [n for n in info.open if n in later_words and not any(n in tables[i] for i in later) and n not in info.own and n not in fn
               and not _recreated(n, [refs[i] for i in later], language, program)]
    lost = missing in words - typed and missing not in typed  # 계획에만 있는 이름이 아직 없다
    loop = lambda text, word: re.search(rf"(^|\s){word}\b", "\n".join(body_lines(text, language, program)))  # noqa: E731
    status, timeout = told.get("status"), told.get("status") == "timeout"
    unchecked = [i for i in sorted(mine) if states[plan.blocks[i].id].verdict == "?"]  # 이 실행에 글이 들어간 확인 전 블록(이대로 넘어가기 등)
    hide = name_hidden(state, index)
    if not timeout and info.params:
        got = Verdict(False, seen=hold_name(info.params, params=True, hide=hide), hint=False, unsure=True)
    elif not timeout and (no_pair or lost):
        # 짝이 없는 이름 하나만 말해 같은 블록을 세 번 확인했다. 어림으로만 이은 이름(굳은 짝·그대로 쓴 이름·앞 블록의 짝은 빼고)도 한 번에 말한다
        unsure = [n for n in info.candidates if n not in no_pair and n in later_words and not any(n in base[i] for i in later) and n not in info.own
                  and n not in fn and not _recreated(n, [refs[i] for i in later], language, program)]
        names = [n for n in info.open if n in no_pair or n in unsure]
        got = Verdict(False, seen=hold_name(names + ([missing] if lost else []), hide=hide), hint=False, unsure=True)
    elif ctx.many_answers and status == "failed":  # 답이 여럿일 수 있는 문제: 예시의 답과 다르다는 것만으로는 맞는지 모른다
        got = Verdict(False, seen=MANY_ANSWERS, hint=False, unsure=True)
    else:
        note = assumed([[m, p] for p, m in guessed.items()], cut, hide)  # 어림 짝으로 이었다면 그 가정을 사실로 말한다. 다 시도하지 못했으면 그 사실도
        got = failure_verdict(told, spans, program, lead, not plan_blocks, note, cut, unchecked, hide)
        # while을 열었다: 시간 초과면 언제나, 그 밖의 실패도 계획이 이 자리를 for로 열고 뒤 블록을 계획 코드로 이었으면(증가가 뒤 블록에 없다)
        if loop(code, "while") and (timeout or (later and loop(refs[index], "for") and not loop(refs[index], "while"))):
            got.seen, got.hint = _add(got.seen, WHILE_NOTE), False
        # 괄호 수가 계획과 다르면 컴파일 오류에 그 사실을 덧붙인다(실행 전에 거부하면 진입 줄 꼴이 다른 맞는 코드를 막았다)
        earlier = [(mine[i], refs[i]) for i in sorted(mine) if i < index]  # 이 실행에 내 글로 들어간 앞 블록(괄호 수는 여기까지 이어서 센다)
        if status in KIND_WORD and (note := brace_note(code, plan.blocks[index], language, program, earlier, hide)):  # 컴파일 오류, 그리고 문법 오류를 실행 오류로 알리는 언어(JavaScript)
            got.seen, got.hint = _add(got.seen, note), False
    rows = [row for row in code.splitlines() if row.strip()]
    if (language == "python" and frame_of(refs[index], language, program)["outer"]
            and all(len(row) - len(row.lstrip()) >= len(rows[0]) - len(rows[0].lstrip()) for row in rows)):
        got.seen, got.hint = _add(got.seen, INDENT_NOTE), False  # 바깥으로 나가는 줄이 있는 블록인데 첫 줄보다 얕은 줄이 없다
    return {"verdict": got, "stored": [], "told": [], "fixes": []}


_SYNTAX = re.compile(r"\b(?:SyntaxError|IndentationError|TabError)\b")


def _place(report: dict, spans: list[dict]) -> tuple[str, int, int, str] | None:
    """오류가 난 줄이 누구의 것인가: (whose(this·mine·tutor), 블록 순번, 내 글의 몇 번째 줄, 그 줄의 글). 줄을 알 수 없으면 None.
    줄은 채점기가 알려 준 것이다(컴파일 오류의 줄, 처음 실행 오류가 난 케이스의 줄)."""
    case = next((c for c in report.get("cases") or [] if c.get("status") == "runtime_error"), None)
    line = report.get("compile_line") if report.get("status") == "compile_error" else (case or {}).get("line")
    span = next((s for s in spans if isinstance(line, int) and s["first"] <= line <= s["last"]), None)
    if span is None:
        return None
    syntax = report.get("status") == "compile_error" or bool(case and _SYNTAX.search(case.get("error") or ""))  # Python·JavaScript의 문법 오류는 실행 오류로 온다
    if span["whose"] == "tutor" and syntax:  # 문법 오류가 튜터 덩이의 첫 줄이고 바로 앞이 내 글이면 내 글이 끝난 자리에서 이어지지 않은 것이다
        at = spans.index(span)
        mine = next((s for s in reversed(spans[:at]) if s["rows"]), None)
        if mine and mine["whose"] != "tutor" and mine["last"] == span["first"] - 1 and line == span["first"] and mine["code"].strip():
            return "join", span["block"], mine["block"], mine["code"].rstrip().split("\n")[-1].strip()
    gap = span.get("gap")  # 시작 코드의 가져오기 줄이 이 덩이 안에 들어갔다: 그 뒤의 줄은 넣은 수만큼 밀려 있다
    if gap and line >= gap[0] - gap[1]:
        if line < gap[0]:
            return "tutor", span["block"], 0, ""
        line -= gap[1]
    idx = line - span["first"]
    n = idx + 1 + span["cut"]
    rows = span["code"].rstrip().split("\n")
    body = span.get("rows") or []
    # 내 글의 그 줄과 실제로 난 줄의 글이 다르면 줄을 잘못 짚은 것이다: 블록의 줄 번호로 말하지 않고 다른 블록의 코드로 말한다
    if span["whose"] != "tutor" and not (0 < n <= len(rows) and idx < len(body) and rows[n - 1].strip() == body[idx].strip()):
        return "other", span["block"], 0, ""
    return span["whose"], span["block"], n, rows[n - 1].strip() if 0 < n <= len(rows) else ""


def failure_verdict(report: dict, spans: list[dict], program: bool, lead: str, alone: bool, assume: str = "", cut: bool = False,
                    unchecked: list[int] = (), hide: bool = False) -> Verdict:
    """이어 돌린 실행이 끝까지 돌았는데 통과하지 못한 판정과 말. '이어지지 않아요'(N)다: 말은 사실(무엇이 났고 어디서 났는가) → 어림 짝을 썼으면 그 짝(assume) →
    두 가지 가능성과 할 수 있는 일(NOT_JOINED). 틀렸다고 단정하지 않는다. alone: 이 프로그램에 튜터의 코드가 없다(내 블록뿐이라 그 사실로 말하고 두 가능성을 말하지 않는다).
    cut: 어림 짝을 다 시도하지 못해 결론을 내지 못했다 → '확인 전'(말은 사실과 그 짝까지).
    unchecked: 이 실행에 글이 들어간 확인 전 블록(순번) → 그 사실을 말하고 '확인 전'(어느 블록 때문인지 모른다. 힌트를 붙이지 않는다).
    hide: 의자에서 이름이 아직 가려진 블록이다. 오류가 내 줄이 아닌 곳(튜터의 코드, 이음매, 모르는 줄)에서 났으면 오류 원문을 싣지 않는다(튜터 코드의 줄과 이름이 든다)."""
    status = report.get("status")
    hint = False
    if status in KIND_WORD:
        row = _error_row(_raw_text(report), first=status == "compile_error", whole=True)
        raw = row if row.endswith(EASY_END) else f"`{row}`"  # 쉬운 말로 바꾼 줄(_easy)은 원문처럼 감싸지 않는다
        place, kind = _place(report, spans), KIND_WORD[status]
        if place is None:
            said = f"{kind}가 났는데 어느 줄에서 났는지는 알 수 없어요."
        elif place[0] == "tutor":
            said = f"튜터의 코드({place[1] + 1}번 블록 자리)에서 {kind}가 났어요."
        elif place[0] == "join":  # 내 블록이 끝난 바로 뒤에서 튜터의 블록이 이어지지 않는다: 튜터의 블록 탓이라 하지 않고 내 블록의 끝을 짚는다
            said = (f"내 {place[2] + 1}번 블록의 마지막 줄(`{_tick(place[3])}`) 뒤에 튜터의 코드({place[1] + 1}번 블록 자리)를 이으면 {kind}가 나요. "
                    f"내 블록의 끝과 다음 블록의 시작이 문법으로 맞물리지 않아요. 내 블록을 어디서 닫았는지 보세요.")
        elif place[0] == "other":
            said = f"다른 블록의 코드에서 {kind}가 났어요."
        else:
            whose = "내 블록" if place[0] == "this" else f"내 {place[1] + 1}번 블록"
            said = f"{whose} {place[2]}번째 줄(`{_tick(place[3])}`)에서 {kind}가 났어요."
        if not (hide and not alone and (place is None or place[0] not in ("this", "mine"))):
            said = f"{said}\n{raw}"
    else:
        said = seen_line(report, program, lead)
        hint = status != "timeout"  # 값이 달랐다: 다음 힌트를 붙인다
    if alone:  # 튜터의 코드와 이은 것이 아니다: '이어지지 않는다'가 아니라 한 일 그대로
        said = f"{ALONE_LEAD} {said}"
    if assume:
        said = _add(said, assume)
    if unchecked:
        said = _add(said, UNCHECKED_IN.format(blocks=", ".join(str(i + 1) for i in unchecked)))
    if cut or unchecked:
        return Verdict(False, seen=said, hint=False, unsure=True)
    return Verdict(False, seen=said if alone else _add(said, NOT_JOINED), hint=hint)


def _add(seen: str, note: str) -> str:
    """말 뒤에 문장을 잇는다. 글상자나 오류 원문 줄(`…`)로 끝난 말 뒤에는 줄을 바꿔서(원문이 어디서 끝나는지 보이게)."""
    return f"{seen}{chr(10) if seen.endswith(('`', EASY_END)) else ' '}{note}"


def _tick(text: str) -> str:
    """코드 글꼴(백틱) 안에 넣을 한 줄."""
    return text.replace("`", "'")


def _raw_text(report: dict) -> str:
    """원문 오류 글: 처음 실패한 케이스의 오류, 없으면 컴파일러 글."""
    case = next((c for c in report.get("cases") or [] if c.get("status") not in ("passed", "skipped")), None)
    return (case or {}).get("error") or report.get("compile") or ""


# 괄호 경계 안내. 어느 괄호인지(그 괄호를 연 줄)를 말한다: '내 블록은 닫았어요' 다음 블록에서 '내 블록은 열어 둔 채'라고 해 서로 반대로 들렸다
BRACE_OPEN = ("튜터의 풀이는 {opener}를 이 블록이 끝날 때도 열어 두고 뒤 블록에서 닫아요. 내 코드는 이 블록이 끝날 때 그 괄호가 열려 있지 않아서, "
              "이어 붙이면 뒤 블록의 `}}`가 남아요. 이 블록은 그 괄호를 열어 둔 채로 끝내 보세요.")
BRACE_CLOSE = ("내 코드는 {opener}가 이 블록이 끝날 때도 열려 있는데, 튜터의 풀이는 그 괄호를 이 블록까지 닫아요. "
               "이어 붙이면 닫히지 않은 괄호가 남아요. 이 블록 안에서 `}}`로 닫아 보세요.")


def _opener(row: str) -> str:
    return f"이 블록에서 연 괄호(`{_tick(row)}`)" if row else "앞에서 연 괄호(`{`)"


def brace_note(code: str, block, language: str, program: bool, earlier: list[tuple[str, str]] = (), hide: bool = False) -> str:
    """중괄호 언어에서 이 블록이 끝날 때 열려 있는 괄호 수가 계획과 다르면 그 안내(실행이 실패한 뒤의 참고 글). Python은 들여쓰기를 틀 정보가 맞춘다.
    계획은 반복을 다음 블록까지 열어 두는데 '}'로 닫아 적은 블록이 통과했고, 모은 코드에 '}'가 하나 더 붙어 컴파일 오류였다.
    earlier: 이 실행에 내 글로 들어간 앞 블록 [(내 글, 계획 코드)]. 괄호 수는 블록 하나가 아니라 여기까지 이어서 견준다
    (앞 블록에서 이미 닫은 사람에게 다음 블록마다 반대 안내를 했다). 중괄호 없는 한 줄 for·if는 차가 같아(0) 여기서 걸리지 않는다.
    hide: 의자에서 이름이 아직 가려진 블록이다. 튜터 코드의 줄은 인용하지 않는다(내 코드의 줄은 그대로)."""
    if language == "python" or not block.reference.strip():
        return ""
    # 여는 괄호가 있는 틀 줄(진입 클래스·함수 머리)이 있으면 그 수는 진입 줄 꼴을 알아보는 규칙에 기댄다: 꼴이 다르면(화살표 함수, std:: 반환형) 틀린 안내였다
    texts = [block.reference, code, *(mine for mine, _ in earlier)]
    if any("{" in row and frame_line(row, language) for text in texts for row in text.splitlines()):
        return ""
    count = lambda text: open_braces(text, language, program)  # noqa: E731
    gap = count(code) - count(block.reference) + sum(count(mine) - count(ref) for mine, ref in earlier)  # 이 블록 끝에서 내 쪽이 더 열어 둔 괄호 수
    if gap < 0:
        return BRACE_OPEN.format(opener="이 블록에서 연 괄호" if hide else _opener(unclosed_row(block.reference, language, program)))
    return BRACE_CLOSE.format(opener=_opener(unclosed_row(code, language, program))) if gap > 0 else ""


def _rows(text: str) -> list[str]:
    """줄 끝 공백과 빈 줄만 뺀 글(실행 없는 통과의 비교)."""
    return [row.rstrip() for row in text.splitlines() if row.strip()]


def check_code(state: MainState, task: str, check=None) -> dict:
    plan = active_plan(state)
    index = current_index(state)
    block = plan.blocks[index]
    language = state["ctx"].language
    code = kept_code(state["request"].code)  # 첫 줄 들여쓰기는 남긴다(바깥으로 나가는 줄을 가늠하는 기준이다)
    digest = code_hash(code)
    states = saved_states(state)
    saved = states.get(block.id)
    table = tables_of(state, plan, passed_pairs(state, plan, skip=index))[index]
    fixes = []
    # 실행 없이 통과하는 길은 하나뿐이다 — 이 자리의 표로 이름을 바꾼 계획 코드와 글자 그대로 같다(줄 끝 공백·빈 줄만 다름. 계획이 예시를 통과했을 때만).
    # 주석·공백·틀 줄을 떼고 견주던 길이 문자열 안의 차이, 블록 가운데의 남는 '}'와 import를 같다고 보아 틀린 코드를 실행 없이 통과시켰다
    if state["request"].skip and found_check(state) is None:  # '이대로 넘어가기': 확인하지 않고 '확인 전'으로 둔 채 다음 블록을 연다
        got, pairs, told_now = Verdict(True, seen=SKIPPED, ran=False), [], []
    elif guide_checked(state) and _rows(code) == _rows(swap_names(block.reference, table, language)):
        got, pairs, told_now = Verdict(True), [], []
    elif (saved is not None and saved.code_hash == digest and check is None  # 채점 함수가 없을 때만 지난 판정을 다시 쓴다
          and saved.verdict in ("Y", "N")):
        got, pairs, told_now = Verdict(saved.verdict == "Y", saved.miss), saved.renames, []
        if not got.ok:  # 채점 함수가 없어 읽고 거절했던 판정을 다시 쓴다: 실행으로 확인한 판정이 아니다
            got.seen, got.ran, got.unsure = f"{unrun_note('')} {UNRUN_NO}", False, True
    else:
        ran = run_verdict(state, plan, index, code, check) or {}
        got = ran.get("verdict")
        if got is None:  # 실행하지 못했다: 모델이 읽고 판정한다. 통과도 거절도 실행으로 확인한 판정과 다르게 말하고, 거절과 형식이 틀린 답은 '확인 전'이다
            got = ask_verdict(code_messages(state, plan, index, code), FOUND_RULE, task) or Verdict(False, malformed=True)
            if got.malformed:
                got = Verdict(False, malformed=True, seen=MALFORMED, hint=False, unsure=True)
            else:
                got.seen, got.ran = unrun_note(ran.get("unrun", "")), False
                if not got.ok:
                    got.seen, got.unsure = f"{got.seen} {UNRUN_NO}", True
        pairs, told_now, fixes = ran.get("stored", []), ran.get("told", []), ran.get("fixes", [])
    pairs = pairs if got.ok else []
    told = {tuple(pair) for item in states.values() for pair in item.renames}  # 이 문제에서 이미 알린 짝은 다시 알리지 않는다
    recheck = found_check(state) is not None  # 앞 블록(의자에서 찾은 블록)을 고쳐 다시 확인한다
    was_kept = saved is not None and saved.verdict in KEPT
    # 통과하지 못했지만 실행이 내 블록의 잘못을 뒷받침하지 못했다(unsure. 실행하지 못해 모델이 읽고 거절한 것도): 틀린 수에 넣지 않는다.
    # 기록은 N으로 둔다(통과하지 못한 글이라 다른 블록을 확인할 때는 계획 코드로 잇는다). 화면은 그 확인 결과를 보고 '확인 전'으로 그린다
    unsure = not got.ok and (got.unsure or not got.ran)
    record = BlockState(
        block_id=block.id,
        code=code,
        code_hash=digest,
        # 다시 확인이 실패하면 그 블록은 '확인 전'으로 둔다(진행은 그대로). 실행하지 못한 통과·넘어가기도 '확인 전'으로 보인다(진행은 한다)
        verdict="Y" if got.ok and got.ran else "?" if got.ok or (recheck and was_kept) else "N",
        miss=got.miss,
        # 틀린 수 + 통과(Y·?면 1). 확인 전의 실패는 틀린 수를 그대로 둔다
        tries=saved.tries if (recheck and was_kept and not got.ok)
        else (saved.tries - (saved.verdict in KEPT) if saved else 0) + (not unsure),
        renames=pairs,
    )
    # 이 블록의 글이 바뀌었으면 그 뒤에 저장된 블록(적어 통과했거나 채운 블록)의 통과를 물린다(글과 진행 위치는 그대로)
    withdrawn = []
    if saved is not None and saved.code_hash != digest:
        for later in plan.blocks[index + 1:]:
            item = states.get(later.id)
            if item is not None and item.verdict == "Y":
                fixes.append(BlockState(item.block_id, item.code, item.code_hash, "?", item.miss, item.tries, item.renames))
                withdrawn.append(item.block_id)
        if withdrawn:  # 다시 확인할 뒤 블록 수는 전에 이미 확인 전이던 것까지 센다(화면의 '확인 전' 칸 수와 같게)
            withdrawn = [b.id for b in plan.blocks[index + 1:] if b.id in withdrawn or (b.id in states and states[b.id].verdict == "?")]
    # 굳은 짝만 알린다(바꿔도 되는 무리의 첫 가정은 알리지 않는다)
    return {"verdict": got, "block_check": record, "renamed": [pair for pair in told_now if tuple(pair) not in told and got.ok], "block_fixes": fixes,
            "withdrawn": withdrawn}
