"""디버그 규칙(모델 없음): 실패 요약, 질문 단계 사다리, 고친 줄 유출 검사."""

import hashlib
import json
import re

LOGIC = ("symptom", "trace", "line", "cause")  # 답이 틀렸을 때: 증상 → 값 따라가기 → 줄 → 원인
ERROR = ("error", "form", "cause")  # 문법·실행 오류: 오류 뜻과 줄 → 같은 문법의 다른 예 → 원인
# 이 단계부터 줄 번호를 화면에 알려 준다. fix: 사용자가 먼저 원인 줄을 짚어 line 단계를 건너뛰어도 그 줄을 확인해 준다
SHOWS_LINE = ("line", "cause", "error", "form", "fix")
# 답(고친 코드)을 달라고 했다: 분명히 거절하고 대안(볼 곳을 좁히는 다음 질문)을 말한다. 의자의 ANSWER_LEAD와 같은 자리
ANSWER_LEAD = "고친 코드는 드리지 않아요. 직접 찾아 고쳐야 다음에 같은 실수를 알아볼 수 있어요. 대신 볼 곳을 좁혀 볼게요. "
FIX_TEXT = "{line}번째 줄을 고친 뒤 같은 입력으로 다시 실행해 보면 무엇이 나올까요?"
FALLBACK = {
    "symptom": "고친 코드로 다시 돌려 보니 아직 기대와 다른 입력이 있어요. 그 입력을 코드 첫 줄부터 손으로 따라가 보면 어디서 달라질까요?",
    "fix": FIX_TEXT,
    "trace": "실패한 입력을 넣고 반복이 돌 때마다 변수 값이 어떻게 바뀌는지 한 줄씩 적어 보면, 어디서 기대와 달라지나요?",
    "line": "{line}번째 줄이 실패한 입력에서 실제로 하는 일과 문제가 요구하는 일은 어떻게 다른가요?",
    "cause": "{line}번째 줄을 다시 볼까요? 그 줄이 실패한 입력에서 어떤 값을 만들고, 어떤 값이 되어야 할까요?",
    "error": "{line}번째 줄에서 오류가 났어요. 그 줄의 괄호, 콜론(:), 들여쓰기, 변수 이름 중 어긋난 것이 있을까요?",
    "form": "{line}번째 줄과 같은 문법을 쓴 다른 줄이나 예전에 쓴 코드와 견주어 보면 무엇이 다른가요?",
}


def fallback(name: str, line) -> str:
    """대체 질문. 줄 번호를 모르면 '의심되는 줄'로 말한다('오류가 난번째 줄'처럼 깨지지 않게)."""
    return FALLBACK[name].replace("{line}번째 줄", f"{line}번째 줄" if line else "의심되는 줄")


def code_hash(code: str) -> str:
    return hashlib.sha256((code or "").strip().encode("utf-8")).hexdigest()


def numbered(code: str) -> str:
    return "\n".join(f"{n:>2}| {line}" for n, line in enumerate((code or "").splitlines(), 1))


def call_text(raw: str) -> str:
    """함수 모드 입력(인자 배열 JSON)을 solution(…) 꼴로. 아니면 그대로."""
    try:
        args = json.loads(raw)
    except (TypeError, ValueError):
        return str(raw).strip()
    if not isinstance(args, list):
        return str(raw).strip()
    return "solution(" + ", ".join(json.dumps(a, ensure_ascii=False) for a in args) + ")"


def first_failure(report: dict) -> dict | None:
    return next((c for c in report.get("cases") or [] if c.get("status") != "passed"), None)


def _error_text(report: dict) -> str:
    case = first_failure(report) or {}
    return str((report.get("compile") or "") or (case.get("error") or ""))


def error_tail(report: dict) -> str:
    """오류 글의 마지막 줄들(Traceback 끝). 임시 폴더 경로는 파일 이름만 남긴다. 없으면 빈 글."""
    lines = [line for line in _error_text(report).strip().splitlines() if line.strip()]
    return re.sub(r'"[^"\n]*[/\\]([^"/\\\n]+)"', r'"\1"', "\n".join(lines[-6:]))


def kind_hint(report: dict) -> str:
    """채점 결과만 보고 가른 종류. 진단(모델)이 다르게 말해도 문법 오류는 이것을 따른다."""
    tail = error_tail(report)
    if re.search(r"SyntaxError|IndentationError|TabError", tail) or report.get("status") == "compile_error":
        return "syntax"
    if tail or report.get("status") == "runtime_error":
        return "runtime"
    return "logic"


def error_line(report: dict) -> int | None:
    """오류가 난 사용자 코드의 줄 번호. 채점기가 준 줄(컴파일 오류의 줄, 실패한 케이스의 줄)을 먼저, 없으면 오류 글에 적힌 것(마지막 것. 사용자 파일 solution·main의 줄을 먼저 본다)."""
    given = report.get("compile_line") or (first_failure(report) or {}).get("line")
    if isinstance(given, int) and not isinstance(given, bool) and given > 0:
        return given
    text = _error_text(report)
    found = re.findall(r'(?:solution|main|Solution|Main)\.\w+"?,? line (\d+)', text) or re.findall(r"line (\d+)", error_tail(report))
    return int(found[-1]) if found else None


def symptom(report: dict) -> str:
    """증상 한 문장. 사용자에게 그대로 보여도 되는 사실만."""
    case = first_failure(report)
    if report.get("status") == "timeout" or (case or {}).get("status") == "timeout":
        return f"{call_text((case or {}).get('input', ''))}가 제한 시간 안에 끝나지 않았어요."
    if case is None:
        return "실행 결과가 기대와 달라요."
    got = str(case.get("got") or "").strip()
    head = f"{call_text(case.get('input', ''))}의 기대한 값은 {case.get('expected')}인데"
    return f"{head} {got}{'이' if batchim(got) else '가'} 나왔어요." if got else f"{head} 아무것도 나오지 않았어요."


def batchim(text: str) -> bool:
    """끝 글자에 받침이 있는가(조사 이·가 고르기. '9이(가) 나왔어요'). 끝의 괄호·따옴표는 건너뛴다.
    숫자는 읽는 소리(영·일·삼·육·칠·팔), 영문은 l·m·n으로 끝나면 받침으로 본다(null → 널, tom → 톰).
    모음 뒤의 p·k·c·b(map → 맵, Vec → 벡), ck(Stack → 스택), que(deque → 덱), 짧은 낱말(4자 이하)의 모음 뒤 t·d(get → 겟, set → 셋)도 받침이다.
    자음 뒤(sort → 소트, append → 어펜드, ArrayList → 어레이리스트)와 g(log → 로그, tag → 태그)는 소리가 갈려 받침으로 보지 않는다.
    끝의 e가 소리 나지 않는 l·m·n + e도 받침이다(name → 네임, line, table. 'name라고'). ng(ㅇ)와 한 글자 r(알)도 받침이다."""
    tail = re.sub(r"[\W_]+$", "", text)
    if not tail:
        return False
    if re.search(r"[lmn]e$|ng$|(?<![A-Za-z])r$|que$|ck$|[aeiou][pkcb]$", tail, re.IGNORECASE):
        return True
    word = re.search(r"[A-Z]?[a-z]*$|[A-Z]+$", tail)[0]  # 낱말의 마지막 도막(HashSet → Set)
    if len(word) <= 4 and re.search(r"[aeiou][td]$", word, re.IGNORECASE):
        return True
    last = tail[-1]
    if "가" <= last <= "힣":
        return (ord(last) - 0xAC00) % 28 > 0
    return last in "013678" if last.isdigit() else last.lower() in "lmn"


def symptom_question(report: dict) -> str:
    return symptom(report) + "\n이 입력을 코드 첫 줄부터 손으로 따라가 보면, 어느 줄에서 값이 기대와 달라지기 시작할까요?"


def ladder(kind: str) -> tuple[str, ...]:
    return LOGIC if kind == "logic" else ERROR


def next_step(kind: str, previous: int | None, found: bool) -> tuple[int, str]:
    """(단계 번호, 단계 이름). previous가 None이면 새 코드다. 원인을 짚었으면 fix."""
    steps = ladder(kind)
    if previous is None:
        return 0, steps[0]
    if found:
        return previous, "fix"
    step = min(previous + 1, len(steps) - 1)
    return step, steps[step]


def said_line(reply: str, code: str) -> int | None:
    """말이 'n번째 줄'을 한 가지 번호로만 짚었으면 그 번호(사용자 코드의 줄 수 안일 때). 말로 짚은 줄이 편집기에 표시되지 않았다."""
    found = {int(n) for n in re.findall(r"(\d+)\s*번째\s*줄", reply or "")}
    if len(found) != 1:
        return None
    line = found.pop()
    return line if 1 <= line <= len((code or "").splitlines()) else None


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def leaks_fix(reply: str, fixed_line: str, code: str) -> bool:
    """말에 고친 줄이 들어 있는가. 사용자 코드에 원래 있던 줄은 유출이 아니다."""
    fixed = _squash(fixed_line)
    if len(fixed) < 5 or fixed in {_squash(line) for line in (code or "").splitlines()}:
        return False
    return fixed in _squash(reply)


PIECE = 6  # 첫 질문에서 고친 줄의 조각으로 보는 길이(공백을 뺀 글자). 'count.get(name, 0) + 1로 바꾸면…'은 줄 전체가 아니라 조각이 샜다
# 줄 번호의 여러 꼴: '4번째 줄', '3번 줄', '4줄', '4행', '3번 라인', '첫 번째 줄', 'line 4'
_UNIT = r"(?:줄(?!어|여|였|었|이면|이려|이는|이고|인)|행(?![렬동위])|라인)"  # '2번 줄이면', '3번 줄어들면', '2번 행렬', '1번 행동'은 줄 번호가 아니다
LINE_WORD = re.compile(rf"\d+\s*(?:번째|번)?\s*{_UNIT}|(?:한|두|세|네|첫|다섯|여섯|일곱|여덟|아홉|열)\s*번째\s*{_UNIT}|\bline\s*\d+", re.IGNORECASE)


def leaks_piece(reply: str, fixed_line: str, code: str) -> bool:
    """고친 줄 가운데 사용자 코드에 없는 조각(PIECE자 이상)이 말에 들어 있는가. 첫 질문에서만 쓴다(뒤 단계는 줄을 짚고 고칠 곳을 묻는다)."""
    fixed, mine, said = _squash(fixed_line), _squash(code), _squash(reply)
    return any(fixed[i:i + PIECE] in said and fixed[i:i + PIECE] not in mine for i in range(len(fixed) - PIECE + 1))


def names_line(reply: str) -> bool:
    """말이 줄 번호를 어떤 꼴로든 말하는가."""
    return bool(LINE_WORD.search(reply or ""))


# 언어 함정: 이 문제·언어에서 실제로 틀리는 것이 증명된 실수(묶음의 traps). 모델에 내놓기 전에 규칙으로 거른다(맞을 수 없는 후보는 보이지 않는다)
# 이 절은 표준 라이브러리만 쓴다: 기본 문제 검사(ui/problemkit.py)가 이 파일을 경로로 읽어 같은 판정으로 증명을 얼리고 확인한다
TRAP_PICKS = 3  # 내놓는 후보 수
# 튜터가 받는 채점 결과는 메모리·출력 초과를 실행 오류로 바꿔 둔다. 증명의 떨어진 상태도 같게 본다
TRAP_STATUS = {"memory_limit": "runtime_error", "output_limit": "runtime_error"}
OUT_CHARS = 40  # 증명이 틀린 답을 낸 케이스의 출력은 이 길이까지 그대로, 넘으면 지문으로 얼린다


def out_key(got) -> str:
    """돌려준 값(함수 방식: 출력의 마지막 줄)을 견줄 꼴로. JSON이면 공백·키 순서를 맞추고, 길면 지문(#sha1 앞 12자리)."""
    lines = str(got or "").strip().splitlines()
    text = lines[-1].strip() if lines else ""
    try:
        text = json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except ValueError:
        pass
    return text if len(text) <= OUT_CHARS else "#" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _term(term: str) -> re.Pattern:
    """이름의 꼴. 낱말 글자로 시작·끝나는 이름은 다른 낱말의 일부(print 속의 int)로 세지 않는다."""
    edge = r"[A-Za-z0-9_]"
    return re.compile((rf"(?<!{edge})" if re.match(r"\w", term[:1]) else "") + re.escape(term) + (rf"(?!{edge})" if re.match(r"\w", term[-1:]) else ""))


def has_term(term: str, code: str) -> bool:
    return _term(term).search(code or "") is not None


# 주석(문자열 안의 #·//는 주석이 아니다). 문자열은 지우지 않는다: 실수한 코드의 이름에 따옴표가 든 것이 있다(== ")
_COMMENT = {"python": re.compile(r"""("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|#[^\n]*"""),
            "other": re.compile(r"""("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|//[^\n]*|/\*.*?\*/""", re.S)}


def without_comments(code: str, language: str) -> str:
    return _COMMENT["python" if language == "python" else "other"].sub(lambda m: m.group(1) or " ", code or "")


def right_count(trap: dict, code: str) -> int:
    """코드(주석 밖)에 고친 꼴의 이름(right)이 나오는 횟수의 합. 묶을 때 정답 풀이에서 센 값(right_base)과 견준다."""
    code = without_comments(code, trap.get("id", "").split(".")[0])
    return sum(len(_term(term).findall(code)) for term in trap.get("right") or [])


def shape_in(trap: dict, code: str) -> bool:
    """함정 항목의 모양 식(shape, 정규식)이 코드(주석 밖)에 맞는가."""
    return re.search(trap["shape"], without_comments(code, trap.get("id", "").split(".")[0])) is not None


def trap_in_code(trap: dict, code: str) -> bool:
    """코드가 그 함정의 꼴인가. 주석은 보지 않는다(주석에 적은 'Reverse로 감싸면…'). 이름 목록은 묶을 때 흔한 낱말과 한 글자를 뺀 것이다.
    - 모양 식(shape)이 있으면: 그 식이 맞는다(이름만으로는 앞으로 도는 size_t 반복과 거꾸로 도는 것을 가르지 못한다).
    - 결과가 정해지지 않은 동작(varies)은 모양 식이 있어야 한다: 케이스 목록이 없어 이름 하나로는 다른 버그와 가를 수 없다.
    - code가 있으면: 실수한 코드에 나타나는 이름(code)이 있다.
    - code가 없는 함정(지우는 꼴의 실수): 고친 꼴의 이름(right)이 그 언어 정답 풀이보다 적게 나온다. 하나만 바꾼 실수(// 하나를 /로)도 잡고,
      정답 풀이만큼 쓴 다른 실수 풀이는 거른다. 정답 풀이의 수(right_base)가 없으면 하나도 없어야 한다."""
    if trap.get("shape"):
        return shape_in(trap, code)
    if trap.get("varies"):
        return False
    if trap.get("code"):
        code = without_comments(code, trap.get("id", "").split(".")[0])
        return any(has_term(term, code) for term in trap["code"])
    if not trap.get("right"):
        return False
    base = trap["right_base"] if isinstance(trap.get("right_base"), int) else 1
    return right_count(trap, code) < base


def trap_candidates(traps: list[dict], report: dict, code: str) -> list[dict]:
    """채점 결과와 코드로 고른 언어 함정 후보(TRAP_PICKS개까지). 통과했거나 자료가 없으면 빈 목록.
    같은 케이스에서 같은 상태로 떨어졌고 코드가 그 함정의 꼴이어야 한다(trap_in_code). 틀린 답(failed)은 돌려준 값까지 증명과 같아야 한다(outs):
    상태만으로는 같은 케이스에서 틀리는 다른 버그와 가를 수 없다. 케이스에 견줄 꼴(out)이 있으면 그것을 쓴다(큰 입력은 내 결과를 줄여 넘긴다). 실행 오류·시간 초과는 상태만 본다.
    결과가 정해지지 않은 동작(varies)은 케이스 목록이 없어 통과하지 못했다는 것만 본다."""
    failed = {str(case.get("id")): case for case in report.get("cases") or [] if case.get("status") != "passed"}
    if not failed or report.get("status") == "passed":
        return []

    def same(trap: dict, cid: str, want: str) -> bool:
        case = failed.get(str(cid))
        if case is None or case.get("status") != TRAP_STATUS.get(want, want):
            return False
        return want != "failed" or (trap.get("outs") or {}).get(str(cid)) == (case.get("out") or out_key(case.get("got")))

    hit = lambda trap: trap.get("varies") or any(same(trap, cid, want) for cid, want in (trap.get("fails") or {}).items())
    return [trap for trap in traps if hit(trap) and trap_in_code(trap, code)][:TRAP_PICKS]


def trap_of(traps: list[dict], trap_id: str) -> dict | None:
    return next((trap for trap in traps if trap_id and trap.get("id") == trap_id), None)
