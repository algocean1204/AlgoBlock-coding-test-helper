"""Kotlin. 함수 모드는 solution 선언의 인자 형을 읽어 FunctionRunner.kt를 만들고 app.jar 하나로 묶는다."""

import re

TOOLS = ("kotlinc", "java")
SAMPLE = {"function": "Solution.kt", "program": "Main.kt"}
ENTRY = {"function": "fun solution", "program": "fun main"}
tm = common = None  # judge.py가 넣는다

SIGNATURE = re.compile(r"fun\s+solution\s*\(([^)]*)\)")

PRINTER = r'''
private fun algoblockQ(s: String): String {
    val b = StringBuilder("\"")
    for (c in s) {
        when {
            c == '"' -> b.append("\\\"")
            c == '\\' -> b.append("\\\\")
            c == '\n' -> b.append("\\n")
            c == '\r' -> b.append("\\r")
            c == '\t' -> b.append("\\t")
            c.code < 0x20 -> b.append(String.format("\\u%04x", c.code))
            else -> b.append(c)
        }
    }
    return b.append('"').toString()
}

private fun algoblockNum(d: Double): String = if (d == Math.rint(d) && Math.abs(d) < 1e15) "${d.toLong()}.0" else d.toString()

private fun algoblockJson(o: Any?): String = when (o) {
    null -> "null"
    is String -> algoblockQ(o)
    is Char -> algoblockQ(o.toString())
    is Double -> algoblockNum(o)
    is Float -> algoblockNum(o.toDouble())
    is Number, is Boolean -> o.toString()
    is IntArray -> o.joinToString(",", "[", "]")
    is LongArray -> o.joinToString(",", "[", "]")
    is DoubleArray -> o.joinToString(",", "[", "]") { algoblockNum(it) }
    is BooleanArray -> o.joinToString(",", "[", "]")
    is CharArray -> o.joinToString(",", "[", "]") { algoblockQ(it.toString()) }
    is Array<*> -> o.joinToString(",", "[", "]") { algoblockJson(it) }
    is Iterable<*> -> o.joinToString(",", "[", "]") { algoblockJson(it) }
    is Map<*, *> -> o.entries.joinToString(",", "{", "}") { algoblockQ(it.key.toString()) + ":" + algoblockJson(it.value) }
    else -> algoblockQ(o.toString())
}
'''


def defines_solution(source):
    return bool(SIGNATURE.search(source))


def defines_main(source):
    return bool(re.search(r"\bfun\s+main\s*\(", source))


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


READER = r"""
private fun algoblockStr(f: String): String = java.io.File(f).readText(Charsets.UTF_8)
private fun algoblockTok(f: String) = java.util.StringTokenizer(algoblockStr(f))
private fun algoblockStrs(f: String): Array<String> { val rows = algoblockStr(f).split("\n"); return Array(rows[0].toInt()) { rows[it + 1] } }
private fun algoblockStrs2(f: String): Array<Array<String>> { val rows = algoblockStr(f).split("\n"); var at = 1; return Array(rows[0].toInt()) { val n = rows[at++].toInt(); Array(n) { rows[at++] } } }
private fun algoblockBools2(f: String): Array<BooleanArray> { val t = algoblockTok(f); return Array(t.nextToken().toInt()) { BooleanArray(t.nextToken().toInt()) { t.nextToken() == "1" } } }
private fun algoblockInts(t: java.util.StringTokenizer) = IntArray(t.nextToken().toInt()) { t.nextToken().toInt() }
private fun algoblockLongs(t: java.util.StringTokenizer) = LongArray(t.nextToken().toInt()) { t.nextToken().toLong() }
private fun algoblockInts(f: String) = algoblockInts(algoblockTok(f))
private fun algoblockLongs(f: String) = algoblockLongs(algoblockTok(f))
private fun algoblockBools(f: String): BooleanArray { val t = algoblockTok(f); return BooleanArray(t.nextToken().toInt()) { t.nextToken() == "1" } }
private fun algoblockInts2(f: String): Array<IntArray> { val t = algoblockTok(f); return Array(t.nextToken().toInt()) { algoblockInts(t) } }
private fun algoblockLongs2(f: String): Array<LongArray> { val t = algoblockTok(f); return Array(t.nextToken().toInt()) { algoblockLongs(t) } }
"""


def read_expr(typ, name):
    """큰 인자를 파일에서 읽는 식(tm.file_text가 쓴 모양)."""
    if typ.base == "string":
        return f'algoblockStr{("", "s", "s2")[typ.dims]}("{name}")'
    word = {"int": "Ints", "long": "Longs", "bool": "Bools"}[typ.base]
    return f'algoblock{word}{"2" if typ.dims == 2 else ""}("{name}")'


def harness(source, args, work):
    params = tm.split_params(SIGNATURE.search(source).group(1))
    types = [tm.kotlin_type(p.split(":", 1)[1].split("=")[0]) for p in params]
    target = "Solution().solution" if re.search(r"\bclass\s+Solution\b", source) else "solution"
    rows = []
    for index, values in enumerate(args):
        if len(values) != len(types):
            raise tm.Unsupported(f"{index + 1}번째 케이스 인자 수 {len(values)}개, 선언 {len(types)}개")
        rows.append(f"        {index} -> {target}(" + ", ".join(tm.argument(tm.kotlin, read_expr, v, t, work, f"case{index}_{n}.txt") for n, (v, t) in enumerate(zip(values, types))) + ")")
    return (
        "fun main(args: Array<String>) {\n    val r: Any? = when (args[0].toInt()) {\n" + "\n".join(rows) +
        "\n        else -> throw IllegalArgumentException(args[0])\n    }\n    println(algoblockJson(r))\n}\n" + PRINTER + READER
    )


def without_main(source):
    """함수 모드: 제출 코드의 main이 있으면 jar 진입점이 둘이 되므로 이름을 바꾼다(실행되지 않는다)."""
    return re.sub(r"\bfun\s+main\s*\(", "fun algoblockUserMain(", source)


def prepare(mode, source, args, work):
    if mode == "function":
        (work / "Solution.kt").write_text(without_main(source), encoding="utf-8")
        (work / "FunctionRunner.kt").write_text(harness(source, args, work), encoding="utf-8")
        return ["kotlinc", "Solution.kt", "FunctionRunner.kt", "-include-runtime", "-d", "app.jar"]
    (work / "Main.kt").write_text(source, encoding="utf-8")
    return ["kotlinc", "Main.kt", "-include-runtime", "-d", "app.jar"]


def command(mode, index):
    jar = ["java", "-Xss256m", *common.JAVA_UTF8, "-jar", "app.jar"]
    return jar + [str(index)] if mode == "function" else jar
