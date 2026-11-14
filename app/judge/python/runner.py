"""Python. 함수 모드는 제출 파일을 모듈로 불러 solution을 부른다(if __name__ 블록은 돌지 않는다)."""

import ast
import json
import os
import re
import shutil

# 사용자 기기의 파이썬. Windows에는 python3이 없거나 스토어로 가는 빈 실행 파일인 경우가 많아 python, py를 먼저 본다
_NAMES = ("python", "py", "python3") if os.name == "nt" else ("python3", "python")
PYTHON = next((name for name in _NAMES if shutil.which(name)), _NAMES[0])
TOOLS = (PYTHON,)
SAMPLE = {"function": "solution.py", "program": "main.py"}
ENTRY = {"function": "def solution", "program": "프로그램으로 돌 코드(맨 위 문장, main, __main__ 블록)"}

HARNESS = """import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("solution", "solution.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
args = json.load(open("cases.json", encoding="utf-8"))[int(sys.argv[1])]
call = getattr(module, "solution", None) or module.Solution().solution  # 맨 위 함수, 없으면 class Solution의 메서드
print(json.dumps(call(*args), ensure_ascii=False))
"""


def _top(nodes):
    """모듈 수준에서 실행되는 문장: if·try·with 안의 문장도 모듈을 불러올 때 실행된다(함수·클래스 안은 아니다)."""
    for node in nodes:
        yield node
        if isinstance(node, (ast.If, ast.Try, ast.With)):
            inner = [*node.body, *getattr(node, "orelse", []), *getattr(node, "finalbody", []), *(s for handler in getattr(node, "handlers", []) for s in handler.body)]
            yield from _top(inner)


def defines_solution(source):
    """하네스가 부를 수 있는 진입 함수: 모듈 수준의 def solution(if·try·with 안 포함), 또는 class Solution 안의 def solution. 다른 이름의 클래스나 함수 안의 solution은 진입이 아니다
    (그 코드를 돌려 AttributeError로 끝냈다. 다른 언어처럼 entry_missing으로 알린다). 문법 오류면 돌려 봐야 오류가 보인다."""
    try:
        body = list(_top(ast.parse(source).body))
    except SyntaxError:
        return bool(re.search(r"^\s*def\s+solution\s*\(", source, re.MULTILINE))
    named = lambda nodes, kind, name: any(isinstance(node, kind) and node.name == name for node in nodes)  # noqa: E731
    return named(body, ast.FunctionDef, "solution") or any(isinstance(node, ast.ClassDef) and node.name == "Solution" and named(node.body, ast.FunctionDef, "solution")
                                                           for node in body)


def defines_main(source):
    """프로그램으로 돌 코드가 있는지. main, __main__ 블록, 표준 입력 읽기. solution이 없는 코드는 맨 위 문장(print 등)도 본다."""
    explicit = r"^\s*def\s+main\s*\(|__name__\s*==\s*['\"]__main__['\"]|\binput\s*\(|sys\.stdin|\bopen\s*\(\s*0\b"
    if re.search(explicit, source, re.MULTILINE):
        return True
    try:
        body = ast.parse(source).body
    except SyntaxError:
        # 돌려 봐야 오류가 보인다. 들여쓰지 않은 줄에서 solution을 부를 때만 프로그램으로도 본다
        if defines_solution(source):
            return bool(re.search(r"^(?!def\b)[^\s#][^#\n]*\bsolution\s*\(", source, re.MULTILINE))
        return True
    if defines_solution(source):
        # solution이 있는 코드의 맨 위 준비 문장(setrecursionlimit, INF = float('inf'))과
        # 함수 안 호출(재귀)은 진입점이 아니다. 맨 위 문장에서 solution을 부를 때만 프로그램으로도 본다.
        top = [node for node in body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        return any(
            isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "solution"
            for node in top for call in ast.walk(node)
        )
    skip = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)
    for node in body:
        if isinstance(node, skip):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # 문서 문자열
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and not _calls(node):
            continue  # 상수 정의
        return True
    return False


def _calls(node):
    return any(isinstance(child, ast.Call) for child in ast.walk(node))


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


def prepare(mode, source, args, work):
    if mode == "function":
        (work / "solution.py").write_text(source, encoding="utf-8")
        (work / "cases.json").write_text(json.dumps(args, ensure_ascii=False), encoding="utf-8")
        (work / "algoblock_runner.py").write_text(HARNESS, encoding="utf-8")
    else:
        (work / "main.py").write_text(source, encoding="utf-8")
    return None


def command(mode, index):
    return [PYTHON, "algoblock_runner.py", str(index)] if mode == "function" else [PYTHON, "main.py"]
