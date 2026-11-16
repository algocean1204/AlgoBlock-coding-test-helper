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
    끝의 e가 소리 나지 않는 l·m·n + e도 받침이다(name → 네임, line, table. 'name라고'). ng(ㅇ)와 한 글자 r(알)도 받침이다."""
    tail = re.sub(r"[\W_]+$", "", text)
    if not tail:
        return False
    if re.search(r"[lmn]e$|ng$|(?<![A-Za-z])r$", tail, re.IGNORECASE):
        return True
    last = tail[-1]
    if "가" <= last <= "힣":
        return (ord(last) - 0xAC00) % 28 > 0
    return last in "013678" if last.isdigit() else last.lower() in "lmn"


def symptom_question(report: dict) -> str:
    return symptom(report) + " 이 입력을 코드 첫 줄부터 손으로 따라가 보면, 어느 줄에서 값이 기대와 달라지기 시작할까요?"


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
