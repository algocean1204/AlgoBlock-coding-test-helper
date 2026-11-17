"""시작 코드: 문제의 params·returns에서 언어별 solution 함수 틀을 만든다. 표준 입출력 문제는 언어별 main 프로그램 뼈대(program_stub).

형 이름은 채점기(app/judge/typemodel.py)가 읽는 것과 같아야 한다. 틀 그대로 내면 컴파일은 되고 답만 틀린다.
자체 확인: python3 ui/stubs.py (형 조합을 5개 언어 채점기에 실제로 돌린다. 없는 도구는 건너뛴다)
"""

LANGUAGES = ("python", "java", "javascript", "cpp", "rust")
NAMES = {
    "java": {"int": "int", "long": "long", "double": "double", "bool": "boolean", "string": "String"},
    "cpp": {"int": "int", "long": "long long", "double": "double", "bool": "bool", "string": "string"},
    "rust": {"int": "i32", "long": "i64", "double": "f64", "bool": "bool", "string": "String"},
}
ZERO = {"int": "0", "long": "0", "double": "0.0", "bool": "false", "string": '""'}


def _split(typ: str) -> tuple[str, int]:
    return typ.replace("[]", ""), typ.count("[]")


def _name(language: str, typ: str) -> str:
    base, dims = _split(typ)
    word = NAMES[language][base]
    if language == "java":
        return word + "[]" * dims
    if language == "cpp":
        for _ in range(dims):
            word = f"vector<{word}>"
        return word
    for _ in range(dims):  # rust
        word = f"Vec<{word}>"
    return word


def _empty(language: str, typ: str) -> str:
    """그 형의 빈 값(틀이 컴파일되게 돌려줄 값)."""
    base, dims = _split(typ)
    if dims == 0:
        if language == "java" and base == "long":
            return "0L"
        if language == "rust" and base == "string":
            return "String::new()"
        return ZERO[base]
    if language == "java":
        return f"new {NAMES['java'][base]}[0]" + "[]" * (dims - 1)
    if language == "cpp":
        return "{}"
    return "Vec::new()"  # rust


def stub(problem: dict, language: str) -> str:
    params, returns = problem["params"], problem["returns"]
    names = [param["name"] for param in params]
    if language == "python":
        return f"def solution({', '.join(names)}):\n    answer = {'[]' if '[]' in returns else {'int': '0', 'long': '0', 'double': '0.0', 'bool': 'False', 'string': chr(34) * 2}[returns]}\n    return answer\n"
    if language == "javascript":
        return f"function solution({', '.join(names)}) {{\n    let answer = {'[]' if '[]' in returns else ZERO[returns]};\n    return answer;\n}}\n"
    typed = [(param["name"], _name(language, param["type"])) for param in params]
    out, empty = _name(language, returns), _empty(language, returns)
    if language == "java":
        args = ", ".join(f"{typ} {name}" for name, typ in typed)
        return f"class Solution {{\n    public {out} solution({args}) {{\n        {out} answer = {empty};\n        return answer;\n    }}\n}}\n"
    if language == "cpp":
        args = ", ".join(f"{typ} {name}" for name, typ in typed)
        return f"#include <string>\n#include <vector>\n\nusing namespace std;\n\n{out} solution({args}) {{\n    {out} answer{'' if '[]' in returns else ' = ' + empty};\n    return answer;\n}}\n"
    if language == "rust":
        args = ", ".join(f"{name}: {typ}" for name, typ in typed)
        return f"fn solution({args}) -> {out} {{\n    let answer: {out} = {empty};\n    answer\n}}\n"
    raise ValueError(f"언어가 아닙니다: {language}")


# 표준 입출력(프로그램 방식) 뼈대: 채점기 runner가 찾는 진입점 그대로(samples/<언어>/program). 틀 그대로 내면 돌기는 하고 답만 틀린다
PROGRAM = {
    "python": "import sys\ninput = sys.stdin.readline\n\n# 여기에 풀이를 써요\n",
    "java": "import java.io.*;\nimport java.util.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n"
            "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        // 여기에 풀이를 써요\n    }\n}\n",
    "javascript": "const input = require(\"fs\").readFileSync(0, \"utf8\");\n\n// 여기에 풀이를 써요\n",
    "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // 여기에 풀이를 써요\n    return 0;\n}\n",
    "rust": "use std::io::{self, Read};\n\nfn main() {\n    let mut input = String::new();\n    io::stdin().read_to_string(&mut input).unwrap();\n    // 여기에 풀이를 써요\n}\n",
}


def program_stub(language: str) -> str:
    return PROGRAM[language]


def demo() -> None:
    import importlib.util
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "judge" / "judge.py"
    spec = importlib.util.spec_from_file_location("algoblock_check_judge", path)
    judge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(judge)
    types = ("int", "long", "double", "bool", "string", "int[]", "long[]", "double[]", "bool[]", "string[]", "int[][]", "long[][]", "double[][]", "string[][]")
    values = {"int": 1, "long": 5_000_000_000, "double": 1.5, "bool": True, "string": "a b", "int[]": [1], "long[]": [5_000_000_000], "double[]": [1.5], "bool[]": [True],
              "string[]": ["a"], "int[][]": [[1]], "long[][]": [[5_000_000_000]], "double[][]": [[1.5]], "string[][]": [["a"]]}
    params = [{"name": f"p{n}", "type": typ} for n, typ in enumerate(types)]
    case = [{"id": "1", "input": json.dumps([values[typ] for typ in types]), "expected": '"틀린 답이어야 한다"'}]
    for language in LANGUAGES:
        for returns in types:
            report = judge.judge(language, stub({"params": params, "returns": returns}, language), case, problem="solution 함수를 완성하세요", mode="function")
            if report["status"] == "toolchain_missing":
                print(language, "도구 없음: 건너뜀")
                break
            assert report["status"] == "failed", (language, returns, report["status"], (report.get("compile") or {}).get("stderr", "")[-400:], report.get("reason"))
        else:
            program = judge.judge(language, program_stub(language), [{"id": "1", "input": "3 5\n", "expected": "틀린 답"}], mode="program")
            assert program["status"] == "failed", (language, program["status"], (program.get("compile") or {}).get("stderr", "")[-400:], program.get("reason"))
            print(language, "ok")


if __name__ == "__main__":
    demo()
