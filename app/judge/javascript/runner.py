"""JavaScript(Node). 함수 모드는 제출 글을 vm으로 돌린 뒤 solution을 부른다. module.exports가 없어도 된다."""

import json
import re

TOOLS = ("node",)
SAMPLE = {"function": "solution.js", "program": "main.js"}
ENTRY = {"function": "solution 함수", "program": "프로그램으로 돌 코드(main, 표준 입력 읽기, solution 없는 코드)"}

HARNESS = r"""const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync("solution.js", "utf8");
const args = JSON.parse(fs.readFileSync("cases.json", "utf8"))[Number(process.argv[2])];
const sandbox = { require, console, process, module: { exports: {} }, exports: {}, Buffer, setTimeout, clearTimeout };
sandbox.module.exports = sandbox.exports;
vm.createContext(sandbox);
vm.runInContext(source + "\n;globalThis.__algoblockSolution = (typeof solution !== 'undefined') ? solution : module.exports.solution;", sandbox, { filename: "solution.js" });
const returned = sandbox.__algoblockSolution(...args);
// BigInt는 JSON.stringify가 예외를 던진다. 수 그대로 찍는다(큰 값을 BigInt로 계산해 돌려주는 풀이)
const text = JSON.stringify(returned, (key, value) => typeof value === "bigint" ? "__algoblockBig__" + value.toString() : value);
console.log(returned === undefined ? "null" : text.replace(/"__algoblockBig__(-?\d+)"/g, "$1"));
"""


def defines_solution(source):
    return bool(re.search(r"\bfunction\s+solution\s*\(|\b(?:const|let|var)\s+solution\s*=|\bsolution\s*:\s*(?:function|\()", source))


def defines_main(source):
    """main, 표준 입력 읽기, 또는 solution 없이 돌 코드가 있으면 프로그램이다(console.log만 있는 프로그램 포함)."""
    if re.search(r"\bfunction\s+main\s*\(|readFileSync\s*\(\s*(?:0|['\"]/dev/stdin['\"])|\breadline\b|process\.stdin", source):
        return True
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.DOTALL).strip()
    return bool(code) and not defines_solution(source)


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


def prepare(mode, source, args, work):
    if mode == "function":
        (work / "solution.js").write_text(source, encoding="utf-8")
        (work / "cases.json").write_text(json.dumps(args, ensure_ascii=False), encoding="utf-8")
        (work / "algoblock_runner.js").write_text(HARNESS, encoding="utf-8")
    else:
        (work / "main.js").write_text(source, encoding="utf-8")
    return None


def command(mode, index):
    return ["node", "algoblock_runner.js", str(index)] if mode == "function" else ["node", "main.js"]
