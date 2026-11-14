"""제출 코드 하나를 채점한다. 모드 정하기 → (없으면 다른 모드로 한 번) → 한 번 빌드 → 케이스마다 실행·비교.

다른 모듈에서 부를 때:
    judge = load("…/judge/judge.py")  # 패키지가 아니라 경로로 불러온다
    judge.judge("python", source, cases, problem="solution 함수를 완성하세요")
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sibling(name):
    """이 폴더의 모듈을 경로로 불러온다. 'common' 같은 흔한 이름이 다른 패키지와 섞이지 않게 고유 이름(algoblock_check_*)으로 둔다."""
    key = f"algoblock_check_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, ROOT / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


common = sibling("common")
typemodel = sibling("typemodel")
TIMEOUT_SECONDS = common.TIMEOUT_SECONDS
TIMEOUT_STREAK = 3  # 시간 초과가 연달아 이만큼 나오면 남은 케이스는 돌리지 않는다(끝없는 반복 하나에 케이스 수 × 제한 시간을 기다리지 않게)
SKIPPED = "앞선 테스트에서 시간 초과가 이어져 돌리지 않았어요."
GRACE = 1.3  # 효율성 케이스는 제한의 이만큼에서 끝낸다(제한을 조금 넘은 것을 끝까지 재 한 번 다시 돌려 보려고)
NEAR = 0.8  # 통과한 효율성 케이스가 제한의 이만큼 이상 걸리면 near

LANGUAGES = ("python", "java", "cpp", "kotlin", "go", "javascript", "rust")
MODES = ("function", "program")

# 한글 조사(solution을, stdin으로) 앞에서도 맞게 영문·숫자 경계만 본다. \b는 한글을 글자로 봐서 놓친다.
_W = r"(?<![A-Za-z0-9_])"
_E = r"(?![A-Za-z0-9_])"
FUNCTION_TEXT = re.compile(rf"{_W}solution{_E}|함수를\s*완성", re.IGNORECASE)
PROGRAM_TEXT = re.compile(
    rf"표준\s*입력|표준\s*출력|{_W}stdin{_E}|{_W}stdout{_E}|첫째\s*줄|둘째\s*줄|입력\s*형식|출력\s*형식|{_W}class\s+Main{_E}|Main\s*클래스",
    re.IGNORECASE,
)

_loaded = {}


def load_language(language):
    if language not in LANGUAGES:
        raise ValueError(f"언어가 아닙니다: {language}")
    if language not in _loaded:
        path = ROOT / language / "runner.py"
        spec = importlib.util.spec_from_file_location(f"algoblock_check_{language}_runner", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.tm, module.common = typemodel, common  # 형 모듈과 실행 도구를 넣어 준다
        _loaded[language] = module
    return _loaded[language]


def decide_mode(problem, source, lang):
    """README 규칙. (모드, 이유). 정할 수 없으면 (None, 이유)."""
    text = problem or ""
    says_function = bool(FUNCTION_TEXT.search(text))
    says_program = bool(PROGRAM_TEXT.search(text))
    if says_function != says_program:
        mode = "function" if says_function else "program"
        return mode, f"문제 설명이 {'solution 함수' if says_function else '표준 입출력·프로그램'}를 가리킴"
    has_solution = lang.defines_solution(source)
    has_main = lang.defines_main(source)
    why = "문제 설명이 두 모드를 같이 가리킴" if says_function else "문제 설명에 모드 단서가 없음"
    if has_solution and not has_main:
        return "function", f"{why}, 코드에 solution만 있음"
    if has_main and not has_solution:
        return "program", f"{why}, 코드에 main만 있음"
    both = "solution과 main이 모두 있음" if has_solution else "solution도 main도 없음"
    return None, f"{why}, 코드에 {both}. 채점하지 않습니다."


def _cases_for(cases, mode):
    if isinstance(cases, dict):
        return cases.get(mode)
    return cases


def _other(mode):
    return "program" if mode == "function" else "function"


def _attempt(lang, mode, index, case, work, seconds, decimal=False):
    """케이스를 한 번 돌리고 답을 비교한다. decimal: 프로그램 모드에서 소수 낱말을 오차 안에서 같게 본다(문제가 실수 답을 허용할 때)."""
    stdin = case["input"] if mode == "program" else ""
    result = common.run_command(lang.command(mode, index), work, stdin, timeout=seconds)
    if result["status"] == "passed":
        same = common.same_function_output(result["stdout"], case["expected"]) if mode == "function" else common.same_program_output(result["stdout"], case["expected"], decimal)
        if not same:
            result["status"] = "failed"
    return result


def _run_case(lang, mode, index, case, work, timeout, decimal=False):
    """케이스에 제한 시간이 있으면(효율성 케이스) 제한의 GRACE배까지 재고, 제한을 넘었지만 스스로 끝났으면 한 번 다시 돌려 짧은 쪽으로 판정한다."""
    limit = case.get("timeout")
    if not limit:
        return _attempt(lang, mode, index, case, work, timeout, decimal)
    result = _attempt(lang, mode, index, case, work, limit * GRACE, decimal)
    if result["status"] != "timeout" and result["time_ms"] > limit * 1000:  # GRACE배에서 끝낸 것은 끝없는 반복일 수 있어 다시 돌리지 않는다
        again = _attempt(lang, mode, index, case, work, limit * GRACE, decimal)
        result = min(result, again, key=lambda one: one["time_ms"])
    if result["status"] == "timeout" or result["time_ms"] > limit * 1000:
        return {**result, "status": "timeout", "time_ms": int(limit * 1000), "near": False}  # 화면은 제한 시간으로 보여 준다
    return {**result, "near": result["status"] == "passed" and result["time_ms"] >= limit * 1000 * NEAR}


def judge(language, source, cases, problem="", mode=None, timeout=TIMEOUT_SECONDS, stop_after=TIMEOUT_STREAK, decimal=False):
    """cases: 고른 모드의 케이스 목록, 또는 {"function": [...], "program": [...]}(다른 모드로 다시 실행할 때 필요).
    stop_after: 시간 초과가 연달아 이만큼 나오면 남은 케이스를 돌리지 않는다(튜터의 블록 코드 확인은 1. 끝나지 않는 반복 하나에 30초).
    decimal: 프로그램 모드에서 기대 출력의 소수 낱말을 1e-6 오차 안에서 같게 본다(문제가 실수 답을 허용할 때만. 기본은 글자 그대로).

    케이스: {"id", "input", "expected"[, "timeout"(초)]}. 함수 모드 input은 인자 배열의 JSON 글, program 모드 input은 표준 입력 글.
    """
    lang = load_language(language)
    report = {"language": language, "mode": None, "fallback_from": None, "status": "", "reason": "", "cases": []}
    absent = lang.toolchain() if hasattr(lang, "toolchain") else common.missing(*lang.TOOLS)
    if absent:
        return {**report, "status": "toolchain_missing", "reason": absent["stderr"]}
    if mode:
        if mode not in MODES:
            raise ValueError(f"모드가 아닙니다: {mode}")
        chosen, reason = mode, "모드를 지정함"
    else:
        chosen, reason = decide_mode(problem, source, lang)
        if chosen is None:
            return {**report, "status": "undecided", "reason": reason}
    if not lang.has_entry(chosen, source):
        other = _other(chosen)
        if lang.has_entry(other, source) and _cases_for(cases, other) is not None and isinstance(cases, dict):
            report["fallback_from"] = chosen
            reason += f". {lang.ENTRY[chosen]}가 없어 {other} 모드로 한 번 다시 실행"
            chosen = other
        else:
            return {**report, "mode": chosen, "status": "entry_missing", "reason": f"{reason}. {lang.ENTRY[chosen]}가 없습니다."}
    report["mode"], report["reason"] = chosen, reason
    mode_cases = _cases_for(cases, chosen) or []
    if not mode_cases:
        return {**report, "status": "no_cases", "reason": f"{chosen} 모드 케이스가 없습니다."}
    with common.work_directory() as directory:
        work = Path(directory)
        try:
            args = [json.loads(case["input"]) for case in mode_cases] if chosen == "function" else None
            build = lang.prepare(chosen, source, args, work)
        except typemodel.Unsupported as error:
            return {**report, "status": "unsupported_signature", "reason": f"호출 코드를 만들 수 없는 선언입니다: {error}"}
        except (json.JSONDecodeError, TypeError) as error:
            return {**report, "status": "bad_case", "reason": f"함수 모드 input은 인자 배열 JSON이어야 합니다: {error}"}
        if build:
            compile_once = getattr(lang, "compile", common.compile_command)
            failure = compile_once(build, work)
            if failure:
                return {**report, "status": failure["status"], "compile": failure,
                        "compile_line": common.error_line(language, lang.SAMPLE[chosen], source, failure["stderr"])}
        streak = 0
        for index, case in enumerate(mode_cases):
            if streak >= stop_after:  # 케이스 수와 순서는 그대로 둔다(통과 수를 센다)
                report["cases"].append({"id": case["id"], "expected": case["expected"], "status": "skipped", "stdout": "", "stderr": SKIPPED, "time_ms": 0, "line": None})
                continue
            result = _run_case(lang, chosen, index, case, work, timeout, decimal)
            result["line"] = common.error_line(language, lang.SAMPLE[chosen], source, result["stderr"]) if result["status"] == "runtime_error" else None
            streak = streak + 1 if result["status"] == "timeout" else 0
            report["cases"].append({"id": case["id"], "expected": case["expected"], **result})
    statuses = [case["status"] for case in report["cases"]]
    report["status"] = next((status for status in statuses if status not in ("passed", "skipped")), "passed")  # 건너뛴 것은 앞선 timeout이 전체 상태가 된다
    return report
