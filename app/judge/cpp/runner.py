"""C++17. 함수 모드는 제출 파일을 #include한 algoblock_main.cpp를 만든다. macOS에서 SDK와 링커가 안 맞으면 다른 SDK로 한 번씩 다시 링크한다."""

import glob
import re
import shutil
import sys

TOOLS = ()  # g++ 또는 clang++ 중 하나. missing은 compiler()가 판단한다
SAMPLE = {"function": "solution.cpp", "program": "main.cpp"}
ENTRY = {"function": "solution 함수", "program": "int main 또는 signed main"}
tm = common = None  # judge.py가 넣는다

SIGNATURE = re.compile(r"([\w:<>,\s&*]+?)\s+solution\s*\(([^)]*)\)\s*\{")
_sysroot = []  # 링크에 성공한 SDK를 한 번 찾으면 기억한다

PRINTER = r"""
static std::string algoblockJson(const std::string& s) {
    std::string out = "\"";
    for (unsigned char c : s) {
        if (c == '"') out += "\\\""; else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n"; else if (c == '\r') out += "\\r"; else if (c == '\t') out += "\\t";
        else if (c < 0x20) { char buf[8]; std::snprintf(buf, sizeof buf, "\\u%04x", c); out += buf; }
        else out += static_cast<char>(c);
    }
    return out + "\"";
}
static std::string algoblockJson(const char* s) { return algoblockJson(std::string(s)); }
static std::string algoblockJson(char c) { return algoblockJson(std::string(1, c)); }
static std::string algoblockJson(bool v) { return v ? "true" : "false"; }
static std::string algoblockJson(int v) { return std::to_string(v); }
static std::string algoblockJson(long v) { return std::to_string(v); }
static std::string algoblockJson(long long v) { return std::to_string(v); }
static std::string algoblockJson(unsigned v) { return std::to_string(v); }
static std::string algoblockJson(unsigned long v) { return std::to_string(v); }
static std::string algoblockJson(unsigned long long v) { return std::to_string(v); }
static std::string algoblockJson(double v) { char buf[64]; std::snprintf(buf, sizeof buf, "%.17g", v); return buf; }
static std::string algoblockJson(const std::vector<bool>& v) {
    std::string out = "[";
    for (std::size_t i = 0; i < v.size(); ++i) { if (i) out += ","; out += v[i] ? "true" : "false"; }
    return out + "]";
}
template <class T> static std::string algoblockJson(const std::vector<T>& v) {
    std::string out = "[";
    for (std::size_t i = 0; i < v.size(); ++i) { if (i) out += ","; out += algoblockJson(v[i]); }
    return out + "]";
}
"""


def compiler():
    return next((name for name in ("g++", "clang++") if shutil.which(name)), None)


def toolchain():
    if compiler():
        return None
    return {"status": "toolchain_missing", "stdout": "", "stderr": "g++ 또는 clang++ 없음", "time_ms": 0}


# clang에는 bits/stdc++.h가 없다. 다른 곳에서 가져온 코드에 흔하므로 작업 폴더에 같은 이름의 헤더를 둔다(-I.).
STDCPP = "\n".join(f"#include <{name}>" for name in (
    "algorithm", "array", "bitset", "cassert", "cctype", "climits", "cmath", "cstdint", "cstdio", "cstdlib", "cstring",
    "deque", "functional", "iomanip", "iostream", "iterator", "limits", "list", "map", "numeric", "queue", "set",
    "sstream", "stack", "string", "tuple", "unordered_map", "unordered_set", "utility", "vector")) + "\n"


def defines_solution(source):
    return bool(SIGNATURE.search(source))


def defines_main(source):
    return bool(re.search(r"\b(?:int|signed)\s+main\s*\(", source))  # #define int long long과 같이 쓰는 signed main


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


def _param_type(param):
    text = re.sub(r"=.*$", "", param).strip()
    found = re.match(r"(.+?)[\s&*]*\b(\w+)$", text)
    return tm.cpp_type(found.group(1) if found else text)


READER = r"""
static std::string algoblockStr(const char* f) { std::ifstream in(f, std::ios::binary); std::stringstream b; b << in.rdbuf(); return b.str(); }
static std::vector<std::string> algoblockStrs(const char* f) { std::ifstream in(f, std::ios::binary); std::string row; std::getline(in, row); std::vector<std::string> out(std::stoul(row)); for (auto& s : out) std::getline(in, s); return out; }
static std::vector<std::vector<std::string>> algoblockStrs2(const char* f) { std::ifstream in(f, std::ios::binary); std::string row; std::getline(in, row); std::vector<std::vector<std::string>> out(std::stoul(row)); for (auto& r : out) { std::getline(in, row); r.resize(std::stoul(row)); for (auto& s : r) std::getline(in, s); } return out; }
template <class T> static std::vector<T> algoblockRow(std::istream& in) { size_t n; in >> n; std::vector<T> out; out.reserve(n); for (size_t i = 0; i < n; i++) { long long x; in >> x; out.push_back((T)x); } return out; }
template <class T> static std::vector<T> algoblockNums(const char* f) { std::ifstream in(f); return algoblockRow<T>(in); }
template <class T> static std::vector<std::vector<T>> algoblockNums2(const char* f) { std::ifstream in(f); size_t n; in >> n; std::vector<std::vector<T>> out; out.reserve(n); for (size_t i = 0; i < n; i++) out.push_back(algoblockRow<T>(in)); return out; }
"""


def read_expr(typ, name):
    """큰 인자를 파일에서 읽는 식(tm.file_text가 쓴 모양)."""
    if typ.base == "string":
        return f'algoblockStr{("", "s", "s2")[typ.dims]}("{name}")'
    element = {"int": "int", "long": "long long", "bool": "bool"}[typ.base]
    return f'algoblockNums{"2" if typ.dims == 2 else ""}<{element}>("{name}")'


def harness(source, args, work):
    found = SIGNATURE.search(source)
    types = [_param_type(p) for p in tm.split_params(found.group(2))]
    rows = []
    for index, values in enumerate(args):
        if len(values) != len(types):
            raise tm.Unsupported(f"{index + 1}번째 케이스 인자 수 {len(values)}개, 선언 {len(types)}개")
        # 인자를 지역 변수로 먼저 만든다. 선언이 vector<int>& 처럼 const 아닌 참조여도 넘길 수 있다.
        locals_ = " ".join(f"{tm.cpp_name(t)} a{n} = {tm.argument(tm.cpp, read_expr, v, t, work, f'case{index}_{n}.txt')};" for n, (v, t) in enumerate(zip(values, types)))
        call = ", ".join(f"a{n}" for n in range(len(types)))
        rows.append(f"        case {index}: {{ {locals_} std::cout << algoblockJson(solution({call})) << \"\\n\"; break; }}")
    return (
        "#include <cstdio>\n#include <cstdlib>\n#include <fstream>\n#include <iostream>\n#include <sstream>\n#include <string>\n#include <vector>\n"
        '#include "solution.cpp"\n' + PRINTER + READER +
        "int main(int argc, char** argv) {\n    switch (std::atoi(argv[1])) {\n" + "\n".join(rows) +
        "\n        default: return 2;\n    }\n    return 0;\n}\n"
    )


def without_main(source):
    """함수 모드: 제출 코드의 main은 호출 코드의 main과 겹치므로 이름을 바꾼다(실행되지 않는다)."""
    return re.sub(r"\b(int|signed)\s+main\s*\(", r"\1 algoblock_user_main(", source)


def prepare(mode, source, args, work):
    tool = compiler()
    (work / "bits").mkdir()
    (work / "bits" / "stdc++.h").write_text(STDCPP, encoding="utf-8")
    if mode == "function":
        (work / "solution.cpp").write_text(without_main(source), encoding="utf-8")
        (work / "algoblock_main.cpp").write_text(harness(source, args, work), encoding="utf-8")
        return [tool, "-std=c++17", "-O2", "-I.", "algoblock_main.cpp", "-o", "app"]
    (work / "main.cpp").write_text(source, encoding="utf-8")
    return [tool, "-std=c++17", "-O2", "-I.", "main.cpp", "-o", "app"]


def _sdks():
    """새 버전부터. 버전이 없는 MacOSX.sdk(기본값을 가리키는 링크)는 뺀다."""
    found = glob.glob("/Library/Developer/CommandLineTools/SDKs/MacOSX*.*.sdk") + glob.glob("/Library/Developer/CommandLineTools/SDKs/MacOSX[0-9]*.sdk")
    found += glob.glob("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX[0-9]*.sdk")

    def version(path):
        digits = re.findall(r"MacOSX([\d.]+)\.sdk", path)
        return tuple(int(x) for x in digits[0].split(".") if x) if digits else ()

    return sorted(set(found), key=version, reverse=True)


def compile(command, work):
    """기본 SDK로 컴파일하고, macOS 링커가 SDK를 읽지 못하면(tapi error) 설치된 다른 SDK로 다시 시도한다."""
    if _sysroot:
        return common.compile_command(command[:1] + ["-isysroot", _sysroot[0]] + command[1:], work)
    failure = common.compile_command(command, work)
    if failure is None or sys.platform != "darwin" or "tapi error" not in failure.get("stderr", ""):
        return failure
    for sdk in _sdks():
        retry = common.compile_command(command[:1] + ["-isysroot", sdk] + command[1:], work)
        if retry is None:
            _sysroot.append(sdk)
            return None
    return failure


def command(mode, index):
    return ["./app", str(index)] if mode == "function" else ["./app"]
