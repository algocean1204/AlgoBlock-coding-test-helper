"""채점 확인 자체 시험. 이 폴더에서 python3 test_check.py 로 돈다. 컴파일러가 없는 언어는 건너뛴다."""

import ctypes
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("algoblock_check_judge", ROOT / "judge.py")
judge = importlib.util.module_from_spec(spec)
sys.modules["algoblock_check_judge"] = judge
spec.loader.exec_module(judge)
common = judge.common

# solution(grid: 정수 2차원 배열, word: 문자열) -> 문자열 배열 [word + 합계]
FUNCTION_CASES = [
    {"id": "1", "input": json.dumps([[[1, 2], [3]], "a"]), "expected": '["a6"]'},
    {"id": "2", "input": json.dumps([[[]], "가\"b"], ensure_ascii=False), "expected": json.dumps(["가\"b0"], ensure_ascii=False)},
]
PROGRAM_CASES = [{"id": "1", "input": "2\n3 4\n", "expected": "7\n"}, {"id": "2", "input": "1\n-5\n", "expected": "-5"}]

SOURCES = {
    "python": {
        "function": "def solution(grid, word):\n    return [word + str(sum(sum(row) for row in grid))]\n",
        "program": "n = int(input())\nprint(sum(map(int, input().split())))\n",
    },
    "javascript": {
        "function": "function solution(grid, word) {\n  return [word + grid.flat().reduce((a, b) => a + b, 0)];\n}\n",
        "program": "const lines = require('fs').readFileSync(0, 'utf8').trim().split('\\n');\nconsole.log(lines[1].split(' ').map(Number).reduce((a, b) => a + b, 0));\n",
    },
    "java": {
        "function": "class Solution {\n    public String[] solution(int[][] grid, String word) {\n        int total = 0;\n        for (int[] row : grid) for (int v : row) total += v;\n        return new String[] {word + total};\n    }\n}\n",
        "program": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        int n = in.nextInt();\n        long total = 0;\n        for (int i = 0; i < n; i++) total += in.nextInt();\n        System.out.println(total);\n    }\n}\n",
    },
    "cpp": {
        "function": "#include <bits/stdc++.h>\nusing namespace std;\nvector<string> solution(vector<vector<int>> grid, string word) {\n    int total = 0;\n    for (auto& row : grid) for (int v : row) total += v;\n    return {word + to_string(total)};\n}\n",
        "program": "#include <iostream>\nint main() {\n    int n; std::cin >> n;\n    long long total = 0;\n    for (int i = 0; i < n; ++i) { int v; std::cin >> v; total += v; }\n    std::cout << total << \"\\n\";\n}\n",
    },
    "kotlin": {
        "function": "class Solution {\n    fun solution(grid: Array<IntArray>, word: String): Array<String> {\n        return arrayOf(word + grid.sumOf { it.sum() })\n    }\n}\n",
        "program": "fun main() {\n    readln()\n    println(readln().split(\" \").sumOf { it.toInt() })\n}\n",
    },
    "go": {
        "function": "package main\n\nimport \"strconv\"\n\nfunc solution(grid [][]int, word string) []string {\n\ttotal := 0\n\tfor _, row := range grid {\n\t\tfor _, v := range row {\n\t\t\ttotal += v\n\t\t}\n\t}\n\treturn []string{word + strconv.Itoa(total)}\n}\n",
        "program": "package main\n\nimport \"fmt\"\n\nfunc main() {\n\tvar n int\n\tfmt.Scan(&n)\n\ttotal := 0\n\tfor i := 0; i < n; i++ {\n\t\tvar v int\n\t\tfmt.Scan(&v)\n\t\ttotal += v\n\t}\n\tfmt.Println(total)\n}\n",
    },
    "rust": {
        "function": "fn solution(grid: Vec<Vec<i32>>, word: String) -> Vec<String> {\n    let total: i32 = grid.iter().map(|r| r.iter().sum::<i32>()).sum();\n    vec![format!(\"{}{}\", word, total)]\n}\n",
        "program": "use std::io::Read;\nfn main() {\n    let mut s = String::new();\n    std::io::stdin().read_to_string(&mut s).unwrap();\n    let nums: Vec<i64> = s.split_whitespace().skip(1).map(|x| x.parse().unwrap()).collect();\n    println!(\"{}\", nums.iter().sum::<i64>());\n}\n",
    },
}

# 실패 종류를 보는 코드(파이썬, C++, 자바)
WRONG = {"python": "def solution(grid, word):\n    return [word]\n"}
CRASH = {"python": "def solution(grid, word):\n    return 1 // 0\n", "java": "class Solution {\n    public int solution(int[][] grid, String word) { int[] a = new int[0]; return a[1]; }\n}\n"}
LOOP = {"python": "def solution(grid, word):\n    while True:\n        pass\n", "cpp": "int solution(std::vector<std::vector<int>> grid, std::string word) { volatile int x = 0; while (true) { x++; } }\n"}
BROKEN = {"cpp": "int solution(std::vector<std::vector<int>> grid, std::string word) { return }\n", "java": "class Solution { public int solution(int[][] grid, String word) { return } }\n",
          "rust": "fn solution(grid: Vec<Vec<i32>>, word: String) -> i32 { grid }\n"}


def available(language):
    lang = judge.load_language(language)
    return (lang.toolchain() if hasattr(lang, "toolchain") else common.missing(*lang.TOOLS)) is None


class CompareTest(unittest.TestCase):
    def test_values(self):
        self.assertTrue(common.same_function_output("6\n", "6"))
        self.assertFalse(common.same_function_output("6.0000001", "6"))  # 기대값이 정수면 오차를 허용하지 않는다
        self.assertFalse(common.same_function_output("true", "1"))
        self.assertTrue(common.same_function_output('["a", 1]', '["a",1]'))
        self.assertFalse(common.same_function_output("[1,2]", "[2,1]"))
        self.assertTrue(common.same_function_output("hello", "hello"))  # JSON이 아니면 글로
        self.assertTrue(common.same_program_output("1 2  \r\n3\n\n", "1 2\n3"))
        self.assertFalse(common.same_program_output("1\n2", "1 2"))
        # 기본은 글자 그대로: 자릿수 형식이 정해진 문제의 다른 형식과 큰 값의 소수 자리 차이를 같게 보지 않는다
        for got, want in (("3.5", "3.50"), ("1", "1.000000"), ("100000.1", "100000.0"), ("2.666666667", "2.666667")):
            self.assertFalse(common.same_program_output(got, want), (got, want))
        # 문제가 실수 답을 허용하면(decimal) 기대 출력에 소수로 적힌 낱말은 1e-6 오차 안에서 같다(자릿수가 달라도). 정수 낱말과 글은 글자 그대로
        self.assertTrue(common.same_program_output("2.666666667\n", "2.666667", decimal=True))
        self.assertTrue(common.same_program_output("avg 2.6666665 km", "avg 2.666667 km", decimal=True))
        self.assertFalse(common.same_program_output("2.67", "2.666667", decimal=True))
        self.assertFalse(common.same_program_output("3.0", "3", decimal=True))  # 기대가 정수면 정확히
        self.assertFalse(common.same_program_output("2.666667  km", "2.666667 km", decimal=True))  # 낱말 사이 공백은 그대로여야 한다
        self.assertFalse(common.same_program_output("abc", "2.5", decimal=True))
        case = [{"id": "1", "input": "", "expected": "0.333333"}]  # 채점기도 문제의 표시대로 비교한다
        self.assertEqual(judge.judge("python", "print(1 / 3)\n", case, mode="program")["status"], "failed")
        self.assertEqual(judge.judge("python", "print(1 / 3)\n", case, mode="program", decimal=True)["status"], "passed")

    def test_float_for_integer_expected(self):
        self.assertTrue(common.same_function_output("3.0", "3"))
        self.assertFalse(common.same_function_output("3.0000001", "3"))
        self.assertFalse(common.same_function_output("2082877144.0", "2082876103"))
        self.assertTrue(common.same_function_output("[5.0, 4.0]", "[5, 4]"))
        self.assertFalse(common.same_function_output("[[5.0], [4.5]]", "[[5], [4]]"))
        self.assertTrue(common.same_function_output("0.30000000000000004", json.dumps(0.1 + 0.2)))
        self.assertTrue(common.same_function_output("0.3", "0.30000001"))  # 기대값이 실수면 지금처럼 오차를 허용한다


class ModeTest(unittest.TestCase):
    def setUp(self):
        self.py = judge.load_language("python")

    def test_problem_text_decides(self):
        only_solution = SOURCES["python"]["function"]
        self.assertEqual(judge.decide_mode("solution 함수를 완성해 주세요.", "", self.py)[0], "function")
        self.assertEqual(judge.decide_mode("첫째 줄에 N이 주어진다. 표준 출력으로", only_solution, self.py)[0], "program")

    def test_code_decides_when_text_is_mixed_or_silent(self):
        mixed = "solution 함수를 완성하세요. 표준 입력으로 주어집니다."
        self.assertEqual(judge.decide_mode(mixed, SOURCES["python"]["function"], self.py)[0], "function")
        self.assertEqual(judge.decide_mode("", SOURCES["python"]["program"], self.py)[0], "program")
        both = SOURCES["python"]["function"] + "\nprint(solution([[1]], input()))\n"
        mode, reason = judge.decide_mode("", both, self.py)
        self.assertIsNone(mode)
        self.assertIn("채점하지 않습니다", reason)

    def test_java_main_class_is_program(self):
        java = judge.load_language("java")
        self.assertEqual(judge.decide_mode("", SOURCES["java"]["program"], java)[0], "program")
        self.assertEqual(judge.decide_mode("", SOURCES["java"]["function"], java)[0], "function")


class LanguageTest(unittest.TestCase):
    def check(self, language, mode):
        if not available(language):
            self.skipTest(f"{language} 컴파일러 없음")
        cases = FUNCTION_CASES if mode == "function" else PROGRAM_CASES
        report = judge.judge(language, SOURCES[language][mode], cases, mode=mode)
        self.assertEqual(report["status"], "passed", json.dumps(report, ensure_ascii=False, indent=1)[:3000])
        self.assertEqual([c["status"] for c in report["cases"]], ["passed", "passed"])

    def test_all_languages_both_modes(self):
        for language in judge.LANGUAGES:
            for mode in judge.MODES:
                with self.subTest(language=language, mode=mode):
                    self.check(language, mode)


class FailureTest(unittest.TestCase):
    def test_wrong_answer(self):
        report = judge.judge("python", WRONG["python"], FUNCTION_CASES, mode="function")
        self.assertEqual([c["status"] for c in report["cases"]], ["failed", "failed"])
        self.assertEqual(report["status"], "failed")

    def test_runtime_error(self):
        for language, source in CRASH.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, FUNCTION_CASES[:1], mode="function")
                self.assertEqual(report["status"], "runtime_error")

    def test_timeout_is_per_case(self):
        for language, source in LOOP.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, FUNCTION_CASES[:1], mode="function", timeout=1)
                self.assertEqual(report["status"], "timeout")
                self.assertEqual(report["cases"][0]["time_ms"], 1000)

    def test_compile_error(self):
        for language, source in BROKEN.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, FUNCTION_CASES[:1], mode="function")
                self.assertEqual(report["status"], "compile_error")
                self.assertTrue(report["compile"]["stderr"])

    def test_fallback_once_to_other_mode(self):
        cases = {"function": FUNCTION_CASES, "program": PROGRAM_CASES}
        report = judge.judge("python", SOURCES["python"]["program"], cases, problem="solution 함수를 완성하세요")
        self.assertEqual((report["fallback_from"], report["mode"], report["status"]), ("function", "program", "passed"))

    def test_no_fallback_without_other_cases(self):
        report = judge.judge("python", SOURCES["python"]["program"], FUNCTION_CASES, problem="solution 함수를 완성하세요")
        self.assertEqual(report["status"], "entry_missing")

    def test_python_entry_is_what_the_runner_calls(self):
        """Python 함수 방식의 진입은 맨 위 def solution이나 class Solution 안의 def solution이다. 다른 클래스·함수 안의 solution은
        다른 언어처럼 entry_missing이다(돌려서 AttributeError로 끝냈다)."""
        method = "class Solution:\n    def solution(self, grid, word):\n        return len(grid) + len(word)\n"
        self.assertEqual(judge.judge("python", method, FUNCTION_CASES[:1], mode="function")["status"], "failed")  # 돌았다(값만 다르다)
        for source in ("class Answer:\n    def solution(self, grid, word):\n        return 0\n", "def outer():\n    def solution(grid, word):\n        return 0\n",
                       "class Solution:\n    def answer(self, grid, word):\n        return 0\n"):
            with self.subTest(source=source):
                self.assertEqual(judge.judge("python", source, FUNCTION_CASES[:1], mode="function")["status"], "entry_missing")
        # 모듈을 불러올 때 실행되는 블록(try·if·with) 안의 def solution은 하네스가 부를 수 있다
        body = "    def solution(grid, word):\n        return len(grid) + len(word)\n"
        for source in (f"try:\n{body}except Exception:\n    pass\n", f"if True:\n{body}", f"import contextlib\nwith contextlib.suppress(Exception):\n{body}"):
            with self.subTest(source=source):
                self.assertEqual(judge.judge("python", source, FUNCTION_CASES[:1], mode="function")["status"], "failed")  # 돌았다(값만 다르다)

    def test_wrong_answer_does_not_fall_back(self):
        cases = {"function": FUNCTION_CASES, "program": PROGRAM_CASES}
        report = judge.judge("python", WRONG["python"], cases, problem="solution 함수를 완성하세요")
        self.assertEqual((report["mode"], report["fallback_from"], report["status"]), ("function", None, "failed"))

    def test_undecided_is_not_judged(self):
        both = SOURCES["python"]["function"] + "\nprint(solution([[1]], input()))\n"
        report = judge.judge("python", both, FUNCTION_CASES)
        self.assertEqual(report["status"], "undecided")
        self.assertEqual(report["cases"], [])

    def test_unsupported_signature_and_bad_case(self):
        source = "import java.util.*;\nclass Solution { public int solution(Map<String, Integer> m) { return 0; } }\n"
        if available("java"):
            report = judge.judge("java", source, [{"id": "1", "input": "[{}]", "expected": "0"}], mode="function")
            self.assertEqual(report["status"], "unsupported_signature")
        report = judge.judge("python", SOURCES["python"]["function"], [{"id": "1", "input": "not json", "expected": "0"}], mode="function")
        self.assertEqual(report["status"], "bad_case")

    def test_no_cases_and_missing_toolchain(self):
        self.assertEqual(judge.judge("python", SOURCES["python"]["function"], [], mode="function")["status"], "no_cases")
        go = judge.load_language("go")
        saved = go.TOOLS
        go.TOOLS = ("algoblock-no-such-tool",)
        try:
            self.assertEqual(judge.judge("go", "", FUNCTION_CASES, mode="function")["status"], "toolchain_missing")
        finally:
            go.TOOLS = saved


class EdgeTest(unittest.TestCase):
    def test_plain_text_expected_matches_string_return(self):
        self.assertTrue(common.same_function_output('"abc"', "abc"))
        self.assertFalse(common.same_function_output("123", "abc"))
        report = judge.judge("python", "def solution(s):\n    return s[::-1]\n", [{"id": "1", "input": '["cba"]', "expected": "abc"}], mode="function")
        self.assertEqual(report["status"], "passed")

    def test_cpp_reference_parameter(self):
        if not available("cpp"):
            self.skipTest("C++ 컴파일러 없음")
        source = "#include <vector>\nusing namespace std;\nlong long solution(vector<int>& v, long long k) { long long t = k; for (int x : v) t += x; return t; }\n"
        report = judge.judge("cpp", source, [{"id": "1", "input": "[[1, 2, 3], 10000000000]", "expected": "10000000006"}], mode="function")
        self.assertEqual(report["status"], "passed", report)

    def test_go_nil_slice_is_empty_array(self):
        if not available("go"):
            self.skipTest("go 없음")
        source = "package main\n\nfunc solution(a []int) []int {\n\tvar out []int\n\tfor _, v := range a {\n\t\tif v > 5 {\n\t\t\tout = append(out, v)\n\t\t}\n\t}\n\treturn out\n}\n"
        report = judge.judge("go", source, [{"id": "1", "input": "[[1, 2]]", "expected": "[]"}, {"id": "2", "input": "[[9]]", "expected": "[9]"}], mode="function")
        self.assertEqual(report["status"], "passed", report)

    def test_typed_returns_across_languages(self):
        """bool, double, long, 2차원 배열 반환."""
        sources = {
            "java": "class Solution { public double[][] solution(long n, boolean flag) { return new double[][]{{n / 2.0}, {flag ? 1.5 : 0}}; } }",
            "kotlin": "class Solution { fun solution(n: Long, flag: Boolean): Array<DoubleArray> = arrayOf(doubleArrayOf(n / 2.0), doubleArrayOf(if (flag) 1.5 else 0.0)) }",
            "rust": "fn solution(n: i64, flag: bool) -> Vec<Vec<f64>> { vec![vec![n as f64 / 2.0], vec![if flag { 1.5 } else { 0.0 }]] }",
            "go": "package main\n\nfunc solution(n int64, flag bool) [][]float64 {\n\tv := 0.0\n\tif flag {\n\t\tv = 1.5\n\t}\n\treturn [][]float64{{float64(n) / 2}, {v}}\n}\n",
            "cpp": "#include <vector>\nstd::vector<std::vector<double>> solution(long long n, bool flag) { return {{n / 2.0}, {flag ? 1.5 : 0.0}}; }",
            "javascript": "function solution(n, flag) { return [[n / 2], [flag ? 1.5 : 0]]; }",
            "python": "def solution(n, flag):\n    return [[n / 2], [1.5 if flag else 0]]\n",
        }
        for language, source in sources.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, [{"id": "1", "input": "[5, true]", "expected": "[[2.5], [1.5]]"}], mode="function")
                self.assertEqual(report["status"], "passed", json.dumps(report, ensure_ascii=False)[:1500])


class ReviewFindingTest(unittest.TestCase):
    """독립 검토에서 찾은 경계(TS 012)."""

    def test_big_integers_are_exact(self):
        self.assertFalse(common.same_function_output("1000000001", "1000000000"))
        self.assertTrue(common.same_function_output("[1,2]", [1, 2]))
        report = judge.judge("python", "def solution(n):\n    return n + 1\n", [{"id": "1", "input": "[1000000000]", "expected": "1000000000"}], mode="function")
        self.assertEqual(report["status"], "failed")

    def test_korean_particles_after_keywords(self):
        py = judge.load_language("python")
        self.assertEqual(judge.decide_mode("solution을 완성하세요.", "", py)[0], "function")
        self.assertEqual(judge.decide_mode("입력은 stdin으로 들어온다.", "", py)[0], "program")
        self.assertIsNone(judge.decide_mode("resolution과 stdinx", "", py)[0])

    def test_programs_without_input(self):
        rows = [("python", 'print("Hello World!")', ""), ("python", "print(open(0).read().strip())", "Hello World!\n"),
                ("javascript", 'console.log("Hello World!")', "")]
        for language, source, stdin in rows:
            with self.subTest(language=language, source=source):
                report = judge.judge(language, source, [{"id": "1", "input": stdin, "expected": "Hello World!"}], problem="표준 입력으로 받은 글을 그대로 출력하세요.")
                self.assertEqual((report["mode"], report["status"]), ("program", "passed"))

    def test_setup_lines_do_not_make_solution_a_program(self):
        problem = "solution 함수를 완성하세요.\n## 입력 형식\n배열이 주어진다."
        for source in ("import sys\nsys.setrecursionlimit(10**6)\ndef solution(a):\n    return sum(a)\n",
                       "INF = float('inf')\ndef solution(a):\n    return sum(a)\n",
                       "def helper(a):\n    return sum(a)\n\ndef solution(a):\n    return helper(a)\n"):
            with self.subTest(source=source):
                report = judge.judge("python", source, [{"id": "1", "input": "[[1, 2]]", "expected": "3"}], problem=problem)
                self.assertEqual((report["mode"], report["status"]), ("function", "passed"))

    def test_recursive_solution_is_function(self):
        problem = "solution 함수를 완성하세요.\n## 입력 형식\nn이 주어진다."
        source = "def solution(n):\n    if n < 2:\n        return n\n    return solution(n - 1) + solution(n - 2)\n"
        for text in (problem, ""):
            with self.subTest(problem=text):
                report = judge.judge("python", source, [{"id": "1", "input": "[5]", "expected": "5"}], problem=text)
                self.assertEqual((report["mode"], report["status"]), ("function", "passed"))
        top_call = source + "print(solution(5))\n"
        self.assertEqual(judge.judge("python", top_call, [{"id": "1", "input": "[5]", "expected": "5"}])["status"], "undecided")

    def test_python_solution_class_method(self):
        source = "class Solution:\n    def solution(self, a, b):\n        return a + b\n"
        report = judge.judge("python", source, [{"id": "1", "input": "[2, 5]", "expected": "7"}], problem="solution 함수를 완성하세요.")
        self.assertEqual((report["mode"], report["status"]), ("function", "passed"))

    def test_cpp_signed_main(self):
        if not available("cpp"):
            self.skipTest("C++ 컴파일러 없음")
        source = "#include <bits/stdc++.h>\n#define int long long\nsigned main() { int a, b; std::cin >> a >> b; std::cout << a + b; }\n"
        report = judge.judge("cpp", source, [{"id": "1", "input": "1 2", "expected": "3"}], problem="첫째 줄에 A와 B가 주어진다.")
        self.assertEqual((report["mode"], report["status"]), ("program", "passed"), report)

    def test_solution_with_main_in_function_mode(self):
        sources = {
            "cpp": "#include <iostream>\nint solution(int a, int b) { return a + b; }\nint main() { std::cout << solution(1, 2); }\n",
            "rust": "fn solution(a: i32, b: i32) -> i32 { a + b }\nfn main() { println!(\"{}\", solution(1, 2)); }\n",
            "go": "package main\n\nimport \"fmt\"\n\nfunc solution(a int, b int) int { return a + b }\n\nfunc main() { fmt.Println(solution(1, 2)) }\n",
            "kotlin": "fun solution(a: Int, b: Int): Int = a + b\nfun main() { println(solution(1, 2)) }\n",
            "java": "class Solution { public int solution(int a, int b) { return a + b; } public static void main(String[] x) { } }",
            "python": "def solution(a, b):\n    return a + b\n\nprint(solution(1, 2))\n",
            "javascript": "function solution(a, b) { return a + b; }\nconsole.log(solution(1, 2));\n",
        }
        for language, source in sources.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, [{"id": "1", "input": "[2, 5]", "expected": "7"}], problem="solution 함수를 완성하세요.")
                self.assertEqual((report["mode"], report["status"]), ("function", "passed"), json.dumps(report, ensure_ascii=False)[:1500])


class SampleTest(unittest.TestCase):
    def test_samples_pass(self):
        run = importlib.util.spec_from_file_location("algoblock_check_run", ROOT / "run.py")
        module = importlib.util.module_from_spec(run)
        run.loader.exec_module(module)
        for language in judge.LANGUAGES:
            with self.subTest(language=language):
                for report in module.run_samples(language, judge.MODES):
                    self.assertIn(report["status"], {"passed", "toolchain_missing"})


# 큰 인자(파일로 넘긴다): solution(nums: long 배열, flags: bool 배열, grid: long 2차원 배열, text: 글, words: 글 배열) -> long
BIG_SOURCES = {
    "python": "def solution(nums, flags, grid, text, words):\n    return sum(nums) + sum(flags) + sum(map(sum, grid)) + len(text) + sum(len(w) for w in words)\n",
    "javascript": "function solution(nums, flags, grid, text, words) {\n  let t = 0;\n  for (const v of nums) t += v;\n  for (const f of flags) if (f) t += 1;\n  for (const r of grid) for (const v of r) t += v;\n  for (const w of words) t += w.length;\n  return t + text.length;\n}\n",
    "java": "class Solution {\n    public long solution(long[] nums, boolean[] flags, long[][] grid, String text, String[] words) {\n        long t = text.length();\n        for (long v : nums) t += v;\n        for (boolean f : flags) if (f) t++;\n        for (long[] r : grid) for (long v : r) t += v;\n        for (String w : words) t += w.length();\n        return t;\n    }\n}\n",
    "cpp": "#include <string>\n#include <vector>\nusing namespace std;\nlong long solution(vector<long long> nums, vector<bool> flags, vector<vector<long long>> grid, string text, vector<string> words) {\n    long long t = text.size();\n    for (long long v : nums) t += v;\n    for (bool f : flags) if (f) t++;\n    for (auto& r : grid) for (long long v : r) t += v;\n    for (auto& w : words) t += w.size();\n    return t;\n}\n",
    "kotlin": "class Solution {\n    fun solution(nums: LongArray, flags: BooleanArray, grid: Array<LongArray>, text: String, words: Array<String>): Long {\n        var t = text.length.toLong()\n        for (v in nums) t += v\n        for (f in flags) if (f) t++\n        for (r in grid) for (v in r) t += v\n        for (w in words) t += w.length\n        return t\n    }\n}\n",
    "go": "package main\n\nfunc solution(nums []int64, flags []bool, grid [][]int64, text string, words []string) int64 {\n\tt := int64(len(text))\n\tfor _, v := range nums {\n\t\tt += v\n\t}\n\tfor _, f := range flags {\n\t\tif f {\n\t\t\tt++\n\t\t}\n\t}\n\tfor _, r := range grid {\n\t\tfor _, v := range r {\n\t\t\tt += v\n\t\t}\n\t}\n\tfor _, w := range words {\n\t\tt += int64(len(w))\n\t}\n\treturn t\n}\n",
    "rust": "fn solution(nums: Vec<i64>, flags: Vec<bool>, grid: Vec<Vec<i64>>, text: &str, words: Vec<&str>) -> i64 {\n    let mut t = text.len() as i64;\n    for v in &nums { t += *v; }\n    for f in &flags { if *f { t += 1; } }\n    for r in &grid { for v in r { t += *v; } }\n    for w in &words { t += w.len() as i64; }\n    t\n}\n",
}


# solution(pairs: 글 2차원 배열, marks: bool 2차원 배열) -> long (원소 수 + 글자 수 + 참의 수)
BIG2_SOURCES = {
    "python": "def solution(pairs, marks):\n    return sum(len(r) for r in pairs) + sum(len(s) for r in pairs for s in r) + sum(map(sum, marks))\n",
    "javascript": "function solution(pairs, marks) {\n  let t = 0;\n  for (const r of pairs) { t += r.length; for (const s of r) t += s.length; }\n  for (const r of marks) for (const m of r) if (m) t += 1;\n  return t;\n}\n",
    "java": "class Solution {\n    public long solution(String[][] pairs, boolean[][] marks) {\n        long t = 0;\n        for (String[] r : pairs) { t += r.length; for (String s : r) t += s.length(); }\n        for (boolean[] r : marks) for (boolean m : r) if (m) t++;\n        return t;\n    }\n}\n",
    "cpp": "#include <string>\n#include <vector>\nusing namespace std;\nlong long solution(vector<vector<string>> pairs, vector<vector<bool>> marks) {\n    long long t = 0;\n    for (auto& r : pairs) { t += r.size(); for (auto& s : r) t += s.size(); }\n    for (auto& r : marks) for (bool m : r) if (m) t++;\n    return t;\n}\n",
    "kotlin": "class Solution {\n    fun solution(pairs: Array<Array<String>>, marks: Array<BooleanArray>): Long {\n        var t = 0L\n        for (r in pairs) { t += r.size; for (s in r) t += s.length }\n        for (r in marks) for (m in r) if (m) t++\n        return t\n    }\n}\n",
    "go": "package main\n\nfunc solution(pairs [][]string, marks [][]bool) int64 {\n\tvar t int64\n\tfor _, r := range pairs {\n\t\tt += int64(len(r))\n\t\tfor _, s := range r {\n\t\t\tt += int64(len(s))\n\t\t}\n\t}\n\tfor _, r := range marks {\n\t\tfor _, m := range r {\n\t\t\tif m {\n\t\t\t\tt++\n\t\t\t}\n\t\t}\n\t}\n\treturn t\n}\n",
    "rust": "fn solution(pairs: Vec<Vec<String>>, marks: Vec<Vec<bool>>) -> i64 {\n    let mut t: i64 = 0;\n    for r in &pairs { t += r.len() as i64; for s in r { t += s.len() as i64; } }\n    for r in &marks { for m in r { if *m { t += 1; } } }\n    t\n}\n",
}


class BigInputTest(unittest.TestCase):
    """큰 인자는 호출 코드에 박지 않고 파일로 넘긴다. Java는 배열 20,000개 리터럴에서 'code too large'로 컴파일이 안 됐다."""

    def test_large_arguments_go_through_files(self):
        nums = [3_000_000_000 + i for i in range(50_000)]
        flags = [i % 3 == 0 for i in range(30_000)]
        grid = [[-(i * j) for j in range(200)] for i in range(200)] + [[]]
        text = "ab" * 60_000
        words = [f"w{i % 97}" for i in range(20_000)] + ["", "last word"]
        expected = sum(nums) + sum(flags) + sum(map(sum, grid)) + len(text) + sum(len(w) for w in words)
        cases = [{"id": "1", "input": json.dumps([nums, flags, grid, text, words], ensure_ascii=False), "expected": str(expected)},
                 {"id": "2", "input": json.dumps([[1], [True], [[2]], "x", ["yz"]]), "expected": "7"}]
        pairs = [[f"k{i % 50}", f"v {i}"] for i in range(30_000)] + [[], ["only"]]
        marks = [[(i + j) % 2 == 0 for j in range(150)] for i in range(150)]
        more = [{"id": "3", "input": json.dumps([pairs, marks]), "expected": str(sum(len(row) for row in pairs) + sum(len(s) for row in pairs for s in row) + sum(map(sum, marks)))}]
        for language, source in BIG2_SOURCES.items():
            if not available(language):
                continue
            with self.subTest(language=language, kind="2차원 글·참거짓"):
                report = judge.judge(language, source, more, problem="solution 함수를 완성하세요")
                self.assertEqual([case["status"] for case in report["cases"]], ["passed"], report.get("compile") or report["cases"])
        for language, source in BIG_SOURCES.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, cases, problem="solution 함수를 완성하세요")
                self.assertEqual([case["status"] for case in report["cases"]], ["passed", "passed"], report.get("compile") or report["cases"])


class BigIntTest(unittest.TestCase):
    def test_javascript_bigint_result_is_printed_as_a_number(self):
        source = "function solution(n) {\n  let t = 1n;\n  for (let i = 0; i < n; i++) t *= 3n;\n  return [t, -t];\n}\n"
        cases = [{"id": "1", "input": "[39]", "expected": json.dumps([3 ** 39, -(3 ** 39)])}]
        self.assertEqual(judge.judge("javascript", source, cases, problem="solution 함수를 완성하세요")["status"], "passed")


class LimitTest(unittest.TestCase):
    """제출 코드가 출력·메모리·프로세스를 마구 써도 채점기가 멈추거나 기기를 채우지 않는다."""

    CASE = [{"id": "1", "input": "[[[1]], \"a\"]", "expected": "1"}]

    def status(self, body, timeout=10):
        report = judge.judge("python", "def solution(grid, word):\n" + body, self.CASE, problem="solution 함수를 완성하세요", timeout=timeout)
        return report["cases"][0]

    def test_endless_output_is_cut(self):
        case = self.status("    while True:\n        print('x' * 1000)\n")
        self.assertEqual(case["status"], "output_limit")
        self.assertLessEqual(len(case["stdout"]), common.OUTPUT_LIMIT)

    def test_memory_bomb_is_stopped(self):
        case = self.status("    blocks = []\n    while True:\n        blocks.append(bytearray(64 * 1024 * 1024))\n")
        self.assertIn(case["status"], ("memory_limit", "runtime_error"))  # 운영체제가 먼저 거절하면 실행 오류다
        self.assertLess(case["time_ms"], 9000)

    def test_children_are_killed_with_the_parent(self):
        marker = Path(common.tempfile.gettempdir()) / "algoblock-check-child-alive.txt"
        marker.unlink(missing_ok=True)
        child = f"import time; time.sleep(4); open({str(marker)!r}, 'w').write('alive')"  # repr: Windows 경로의 \U가 이스케이프로 읽히지 않게
        body = ("    import subprocess, sys\n"
                f"    subprocess.Popen([sys.executable, '-c', {child!r}])\n"
                "    while True:\n        pass\n")
        self.assertEqual(self.status(body, timeout=2)["status"], "timeout")
        common.time.sleep(4)
        self.assertFalse(marker.exists(), "시간 초과 뒤에도 자식 프로세스가 살아 있다")

    def test_waiting_for_input_ends(self):
        self.assertEqual(self.status("    return int(input() or 1)\n")["status"], "runtime_error")  # 입력이 없다: 기다리지 않고 끝난다

    def test_secrets_are_not_passed(self):
        source = "import os\ndef solution(grid, word):\n    return [os.environ.get('ANTHROPIC_API_KEY', ''), os.environ.get('ALGOBLOCK_UI_DATA', ''), bool(os.environ.get('PATH'))]\n"
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x", "ALGOBLOCK_UI_DATA": "y"}):
            report = judge.judge("python", source, [{"id": "1", "input": "[[[1]], \"a\"]", "expected": '["", "", true]'}], mode="function")
        self.assertEqual(report["status"], "passed", report["cases"])

    @unittest.skipIf(os.name == "nt", "프로세스 그룹은 POSIX에서만 본다")
    def test_children_are_killed_after_normal_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            note = Path(folder) / "pid.txt"
            body = ("    import subprocess\n"
                    "    child = subprocess.Popen(['sleep', '300'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                    f"    open(r'{note}', 'w').write(str(child.pid))\n    return 1\n")
            self.assertEqual(self.status(body)["status"], "passed")
            pid = int(note.read_text())
        for _ in range(20):  # 고아는 init이 거둔다. 거둘 때까지 잠깐 기다린다
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            common.time.sleep(0.1)
        self.fail("정상 종료 뒤에도 자식 프로세스가 살아 있다")

    def test_child_holding_stdout_does_not_block(self):
        started = common.time.monotonic()
        case = self.status("    import subprocess, sys\n    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'])\n    return 1\n")
        self.assertEqual(case["status"], "passed", case)
        self.assertLess(common.time.monotonic() - started, 3)

    def test_kill_running_ends_a_running_command(self):
        result = []
        thread = common.threading.Thread(target=lambda: result.append(common.run_command([sys.executable, "-c", "while True: pass"], ROOT, timeout=60)))
        thread.start()
        for _ in range(50):
            if common.RUNNING:
                break
            common.time.sleep(0.1)
        (process,) = list(common.RUNNING)
        common.kill_running()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertIsNotNone(process.poll(), "kill_running 뒤에도 프로세스가 살아 있다")
        self.assertEqual(common.RUNNING, set())

    def test_cpu_limit_ends_a_loop_nobody_kills(self):  # POSIX는 RLIMIT_CPU, Windows는 작업 객체가 끝낸다
        self.assertEqual(common.cpu_limit(1), 9)
        self.assertEqual(common.cpu_limit(0.65), 8)
        started = common.time.monotonic()
        result = common.run_command([sys.executable, "-c", "while True: pass"], ROOT, timeout=60, cpu_seconds=1)  # 벽시계 제한은 크게: 상한이 끝낸다
        self.assertEqual(result["status"], "runtime_error", result)
        self.assertLess(common.time.monotonic() - started, 10)

    def test_endless_loop_stops_after_timeouts(self):
        cases = [{"id": str(i), "input": "[[[1]], \"a\"]", "expected": "1"} for i in range(6)]
        started = common.time.monotonic()
        report = judge.judge("python", LOOP["python"], cases, mode="function", timeout=1)
        self.assertLess(common.time.monotonic() - started, judge.TIMEOUT_STREAK * 1 + 3)
        self.assertEqual([c["status"] for c in report["cases"]], ["timeout"] * 3 + ["skipped"] * 3)
        self.assertEqual(report["status"], "timeout")  # 건너뛴 것은 전체 상태가 되지 않는다
        self.assertEqual([c["id"] for c in report["cases"]], [c["id"] for c in cases])
        self.assertEqual([(c["time_ms"], c["stderr"]) for c in report["cases"][3:]], [(0, judge.SKIPPED)] * 3)
        report = judge.judge("python", LOOP["python"], cases, mode="function", timeout=1, stop_after=1)  # 튜터의 블록 코드 확인(30초)
        self.assertEqual([c["status"] for c in report["cases"]], ["timeout"] + ["skipped"] * 5)

    def test_streak_resets_after_other_result(self):
        source = "def solution(n):\n    while n == 0:\n        pass\n    return n\n"
        cases = [{"id": str(i), "input": f"[{n}]", "expected": str(n)} for i, n in enumerate((0, 0, 1, 0, 0))]
        report = judge.judge("python", source, cases, mode="function", timeout=1)
        self.assertEqual([c["status"] for c in report["cases"]], ["timeout", "timeout", "passed", "timeout", "timeout"])


class JobEventsTest(unittest.TestCase):
    """작업의 알림으로 결과를 다듬는 판정(포트 없이 함수만 부른다. 어느 OS에서나 돈다)."""

    def test_process_limit_adds_one_line_unless_passed(self):
        events = {common.JOB_MSG_ACTIVE_PROCESS_LIMIT}
        failed = common._apply_job_events({"status": "runtime_error", "stdout": "", "stderr": "Traceback\n"}, events, 64)
        self.assertEqual((failed["status"], failed["stderr"]), ("runtime_error", "Traceback\n프로세스 수 상한(64)에 걸렸어요\n"))
        self.assertEqual(common._apply_job_events({"status": "runtime_error", "stderr": ""}, events, 64)["stderr"], "프로세스 수 상한(64)에 걸렸어요\n")
        self.assertEqual(common._apply_job_events({"status": "runtime_error", "stderr": "끝에 줄바꿈 없음"}, events, 64)["stderr"], "끝에 줄바꿈 없음\n프로세스 수 상한(64)에 걸렸어요\n")
        passed = {"status": "passed", "stdout": "ok", "stderr": ""}
        self.assertEqual(common._apply_job_events(passed, events, 64), passed)
        self.assertEqual(common._apply_job_events({"status": "runtime_error", "stderr": "x"}, set(), 64)["stderr"], "x")  # 알림이 없으면 그대로

    def test_memory_event_decides_memory_limit_only_for_runtime_error(self):
        events = {common.JOB_MSG_JOB_MEMORY_LIMIT}
        self.assertEqual(common._apply_job_events({"status": "runtime_error", "stderr": ""}, events, 64)["status"], "memory_limit")
        self.assertEqual(common._apply_job_events({"status": "timeout", "stderr": ""}, events, 64)["status"], "timeout")


class WindowsShapeTest(unittest.TestCase):
    """Windows API에 넘기는 구조체의 크기와 자리(Microsoft 문서의 x64 배치). 순수 ctypes라 어느 64비트 OS에서나 돈다."""

    @unittest.skipUnless(ctypes.sizeof(ctypes.c_void_p) == 8, "64비트에서만 본다")
    def test_structures_match_windows_x64(self):
        self.assertEqual(ctypes.sizeof(common.JobBasicLimit), 64)
        self.assertEqual([getattr(common.JobBasicLimit, name).offset for name in ("PerJobUserTimeLimit", "LimitFlags", "MinimumWorkingSetSize", "ActiveProcessLimit", "Affinity", "SchedulingClass")],
                         [8, 16, 24, 40, 48, 60])
        self.assertEqual(ctypes.sizeof(common.JobIoCounters), 48)
        self.assertEqual(ctypes.sizeof(common.JobExtendedLimit), 144)
        self.assertEqual([getattr(common.JobExtendedLimit, name).offset for name in ("IoInfo", "ProcessMemoryLimit", "JobMemoryLimit", "PeakJobMemoryUsed")], [64, 112, 120, 136])
        self.assertEqual(ctypes.sizeof(common.JobCompletionPort), 16)
        self.assertEqual(common.JobCompletionPort.CompletionPort.offset, 8)
        self.assertEqual(ctypes.sizeof(common.ThreadEntry), 28)
        self.assertEqual(common.ThreadEntry.th32OwnerProcessID.offset, 12)

    def test_windows_program_path(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(common._windows_program(["./app", "1"], folder), [str(Path(folder) / "app"), "1"])  # 없으면 이름 그대로(실행이 FileNotFoundError를 낸다)
            (Path(folder) / "app").write_bytes(b"")
            self.assertEqual(common._windows_program(["./app"], folder), [str(Path(folder) / "app")])  # go·rustc는 이름 그대로 만든다
            (Path(folder) / "app.exe").write_bytes(b"")
            self.assertEqual(common._windows_program(["./app", "1"], folder), [str(Path(folder) / "app.exe"), "1"])  # g++(MinGW)는 .exe를 붙인다
        self.assertEqual(common._windows_program([Path(sys.executable).name, "-c", "1"], ROOT)[1:], ["-c", "1"])


@unittest.skipUnless(os.name == "nt", "Windows 작업 객체 시험은 Windows에서만 돈다")
class WindowsJobTest(unittest.TestCase):
    """Windows: 제출 코드는 작업 객체 안에서 돈다. 정상 종료 뒤의 자식, CPU 시간, 커밋 메모리를 작업이 막는다."""

    def run_python(self, code, **limits):
        return common.run_command([sys.executable, "-c", code], ROOT, **limits)

    def test_job_is_used(self):
        result = self.run_python("print('ok')")
        self.assertEqual((result["status"], result["stdout"].strip()), ("passed", "ok"), result)
        self.assertNotIn("warning", result)

    def test_children_are_killed_after_normal_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "alive.txt"
            child = f"import time; time.sleep(3); open(r'{marker}', 'w').write('alive')"
            parent = f"import subprocess, sys; subprocess.Popen([sys.executable, '-c', {child!r}], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"
            self.assertEqual(self.run_python(parent)["status"], "passed")
            common.time.sleep(4.5)
            self.assertFalse(marker.exists(), "주 프로세스가 끝난 뒤에도 자식 프로세스가 살아 있다")

    def test_commit_memory_is_capped(self):
        """한 번에 크게 잡으면 작업 집합을 재기 전에 커밋 상한이 할당을 거절한다. 작업의 알림으로 memory_limit라고 판정한다(POSIX와 같은 이름)."""
        big = common.MEMORY_LIMIT_MB * common.JOB_MEMORY_FACTOR + 1024  # 작업의 커밋 상한보다 1GB 크게 한 번에
        result = self.run_python(f"b = bytearray({big} * 2**20); print(len(b))")
        self.assertEqual(result["status"], "memory_limit", result)
        self.assertIn("MemoryError", result["stderr"])
        plain = self.run_python("raise SystemExit(3)")  # 메모리와 상관없는 실패는 그대로 실행 오류다
        self.assertEqual(plain["status"], "runtime_error", plain)

    # 자식을 count개 띄우고(5초 잠드는 파이썬) 1.5초 뒤 만들지 못했거나 이미 끝난 수를 출력하는 코드. 상한을 넘은 프로세스는 만들기가 실패하거나 바로 끝난다
    SPAWN = ("import subprocess, sys, time\nkids, fails = [], 0\nfor _ in range({count}):\n    try:\n"
             "        kids.append(subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))\n"
             "    except OSError:\n        fails += 1\ntime.sleep(1.5)\nfails += sum(kid.poll() is not None for kid in kids)\nfor kid in kids:\n    kid.kill()\nprint(fails)\n")

    def test_process_count_is_capped(self):
        """작업 안의 동시 프로세스 수가 상한을 넘으면 그 프로세스를 만들지 못한다. 상한을 끄면(processes=None) 모두 만들어진다."""
        capped = self.run_python(self.SPAWN.format(count=8), processes=4)
        self.assertEqual(capped["status"], "passed", capped)
        self.assertGreaterEqual(int(capped["stdout"]), 1, "상한(4)을 넘는 자식이 만들어졌다")
        free = self.run_python(self.SPAWN.format(count=8), processes=None)
        self.assertEqual((free["status"], free["stdout"].strip()), ("passed", "0"), free)

    def test_default_process_limit_allows_a_few_children(self):
        """기본 상한은 자식 몇 개를 띄우는 코드를 막지 않는다."""
        result = self.run_python(self.SPAWN.format(count=5))
        self.assertEqual((result["status"], result["stdout"].strip()), ("passed", "0"), result)

    def test_error_dialogs_are_off_in_the_child_and_restored_after(self):
        """자식은 오류 창을 끈 오류 모드(SetErrorMode)로 돈다. 이 프로세스의 오류 모드는 실행이 끝나면 원래대로다."""
        kernel = common._kernel32()
        original = kernel.SetErrorMode(0)  # 읽으면서 0으로 둔다: 아래에서 자식이 0이 아니면 run_command가 켠 것이다
        try:
            result = self.run_python("import ctypes; print(ctypes.windll.kernel32.SetErrorMode(0))")
            after = kernel.GetErrorMode()
        finally:
            kernel.SetErrorMode(original)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(int(result["stdout"]) & common.ERROR_MODE, common.ERROR_MODE, result)
        self.assertEqual(after, 0, "실행이 끝난 뒤 이 프로세스의 오류 모드가 되돌려지지 않았다")

    def test_process_limit_line_is_added_to_a_failed_run_only(self):
        """작업이 '프로세스 수 상한' 알림을 보냈다고 하면(알림만 고정한다) 실패한 실행의 stderr 끝에 한 줄이 붙고, 통과한 실행에는 붙지 않는다."""
        line = f"프로세스 수 상한({common.JOB_PROCESS_LIMIT})에 걸렸어요"
        with mock.patch.object(common, "_job_events", return_value={common.JOB_MSG_ACTIVE_PROCESS_LIMIT}):
            failed = self.run_python("raise SystemExit(1)")
            passed = self.run_python("print('ok')")
        self.assertEqual(failed["status"], "runtime_error", failed)
        self.assertTrue(failed["stderr"].endswith(line + "\n"), failed)
        self.assertEqual(passed["status"], "passed", passed)
        self.assertNotIn(line, passed["stderr"])

    def test_without_job_it_still_runs_and_says_so(self):
        with mock.patch.object(common, "_windows_job", side_effect=OSError(5, "막힘")):
            result = self.run_python("print('ok')")
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["warning_kind"], "no_job")
        self.assertIn("막힘", result["warning"])

    def test_not_started_is_a_runtime_error_and_says_so(self):
        with mock.patch.object(common, "_resume", side_effect=OSError(5, "재개 안 됨")):
            result = self.run_python("print('ok')")
        self.assertEqual((result["status"], result["warning_kind"]), ("runtime_error", "not_started"), result)
        self.assertIn("재개 안 됨", result["warning"])


class EfficiencyTest(unittest.TestCase):
    """효율성 케이스(제한 시간이 있는 케이스)는 제한의 GRACE배까지 재고, 넘었지만 스스로 끝났으면 한 번 다시 돌린다."""

    def run_one(self, body):
        case = [{"id": "1", "input": "[1]", "expected": "1", "timeout": 1}]
        started = common.time.monotonic()
        report = judge.judge("python", "import time\ndef solution(n):\n" + body + "    return n\n", case, mode="function")
        return report["cases"][0], common.time.monotonic() - started

    def test_fast_is_not_near(self):
        case, _ = self.run_one("    time.sleep(0.5)\n")
        self.assertEqual(case["status"], "passed")
        self.assertFalse(case.get("near"))

    def test_close_to_limit_is_near(self):
        case, _ = self.run_one("    time.sleep(0.85)\n")
        self.assertEqual((case["status"], case.get("near")), ("passed", True), case)

    def test_slow_first_run_is_tried_again(self):
        with tempfile.TemporaryDirectory() as folder:
            note = Path(folder) / "count.txt"
            case, _ = self.run_one(f"    import os\n    first = not os.path.exists(r'{note}')\n    open(r'{note}', 'a').write('x')\n"
                                   "    time.sleep(1.1 if first else 0.7)\n")
            self.assertEqual(note.read_text(), "xx")
        self.assertEqual(case["status"], "passed", case)
        self.assertLess(case["time_ms"], 1000)

    def test_always_over_limit_is_timeout(self):
        case, _ = self.run_one("    time.sleep(1.2)\n")
        self.assertEqual((case["status"], case["time_ms"]), ("timeout", 1000))

    def test_endless_loop_is_not_tried_again(self):
        case, spent = self.run_one("    while True:\n        pass\n")
        self.assertEqual((case["status"], case["time_ms"]), ("timeout", 1000))
        self.assertLess(spent, 2.2)  # GRACE배(1.3초)에서 한 번만 죽인다


# 3번째 줄에서 실행 오류, 2번째 줄에서 컴파일(문법) 오류. 함수 모드 solution(a: 정수)
CRASH_AT_3 = {
    "python": "def solution(a):\n    b = [a]\n    return b[5]\n",
    "java": "class Solution {\n    public int solution(int a) {\n        int[] b = new int[0]; return b[a];\n    }\n}\n",
    "kotlin": "class Solution {\n    fun solution(a: Int): Int {\n        return IntArray(0)[a]\n    }\n}\n",
    "javascript": "function solution(a) {\n  const o = null;\n  return o.x;\n}\n",
    "go": "package main\nfunc solution(a int) int {\n\treturn []int{}[a]\n}\n",
    "rust": "fn solution(a: i32) -> i32 {\n    let v: Vec<i32> = Vec::new();\n    v[a as usize]\n}\n",
}
BROKEN_AT_2 = {
    "python": "def solution(a):\n    return a +\n",
    "javascript": "function solution(a) {\n  return a +;\n}\n",
    "java": "class Solution {\n    public int solution(int a) { return a }\n}\n",
    "kotlin": "fun solution(a: Int): Int {\n    return undefinedName\n}\n",
    "cpp": "int solution(int a) {\n    return a +;\n}\n",
    "go": "package main\nfunc solution(a int) int { return a + }\n",
    "rust": "use std::collections::HashMap;\nfn solution(a: i32) -> i32 { undefined_name }\n",  # 앞 줄의 경고(쓰지 않는 use)를 오류로 읽지 않는다
}


class ErrorLineTest(unittest.TestCase):
    CASE = [{"id": "1", "input": "[1]", "expected": "1"}]

    def test_runtime_error_line(self):
        for language, source in CRASH_AT_3.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                case = judge.judge(language, source, self.CASE, mode="function")["cases"][0]
                self.assertEqual((case["status"], case["line"]), ("runtime_error", 3), case["stderr"][-800:])

    def test_compile_or_syntax_error_line(self):
        for language, source in BROKEN_AT_2.items():
            if not available(language):
                continue
            with self.subTest(language=language):
                report = judge.judge(language, source, self.CASE, mode="function")
                line = report["cases"][0]["line"] if report["cases"] else report.get("compile_line")
                self.assertEqual(line, 2, json.dumps(report, ensure_ascii=False)[-1500:])

    def test_python_line_is_last_user_frame(self):
        report = judge.judge("python", "import heapq\ndef solution(a):\n    return heapq.nlargest(1, a)\n", self.CASE, mode="function")
        self.assertIn("heapq.py", report["cases"][0]["stderr"])
        self.assertEqual(report["cases"][0]["line"], 3)
        program = judge.judge("python", "n = int(input())\nprint(n)\nprint([][n])\n", [{"id": "1", "input": "1\n", "expected": "1"}], mode="program")
        self.assertEqual(program["cases"][0]["line"], 3)

    def test_runner_side_line_is_none(self):
        report = judge.judge("python", "def solution(a, b):\n    return a\n", self.CASE, mode="function")  # 인자 수가 달라 호출 코드에서 난 오류
        self.assertEqual((report["cases"][0]["status"], report["cases"][0]["line"]), ("runtime_error", None))
        self.assertIsNone(common.error_line("javascript", "solution.js", "x\n", "solution.js:9"))


if __name__ == "__main__":
    unittest.main()
