"""Java. 함수 모드는 solution 선언의 인자 형을 읽어 케이스마다 리터럴로 부르는 FunctionRunner.java를 만든다."""

import re

TOOLS = ("javac", "java")
SAMPLE = {"function": "Solution.java", "program": "Main.java"}
ENTRY = {"function": "class Solution의 solution 메서드", "program": "class Main의 main 메서드"}
tm = common = None  # judge.py가 넣는다

SIGNATURE = re.compile(r"([\w\[\]<>, ]+?)\s+solution\s*\(([^)]*)\)\s*(?:throws[^{]*)?\{")

PRINTER = r"""
    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"') b.append("\\\""); else if (c == '\\') b.append("\\\\");
            else if (c == '\n') b.append("\\n"); else if (c == '\r') b.append("\\r"); else if (c == '\t') b.append("\\t");
            else if (c < 0x20) b.append(String.format("\\u%04x", (int) c)); else b.append(c);
        }
        return b.append('"').toString();
    }
    static String algoblockJson(Object o) {
        if (o == null) return "null";
        if (o instanceof String || o instanceof Character) return q(o.toString());
        if (o instanceof Double || o instanceof Float) {
            double d = ((Number) o).doubleValue();
            return d == Math.rint(d) && Math.abs(d) < 1e15 ? (long) d + ".0" : Double.toString(d);
        }
        if (o instanceof Number || o instanceof Boolean) return o.toString();
        if (o.getClass().isArray()) {
            StringBuilder b = new StringBuilder("[");
            for (int i = 0; i < java.lang.reflect.Array.getLength(o); i++) {
                if (i > 0) b.append(',');
                b.append(algoblockJson(java.lang.reflect.Array.get(o, i)));
            }
            return b.append(']').toString();
        }
        if (o instanceof Iterable) {
            StringBuilder b = new StringBuilder("[");
            boolean first = true;
            for (Object item : (Iterable<?>) o) { if (!first) b.append(','); first = false; b.append(algoblockJson(item)); }
            return b.append(']').toString();
        }
        if (o instanceof java.util.Map) {
            StringBuilder b = new StringBuilder("{");
            boolean first = true;
            for (java.util.Map.Entry<?, ?> e : ((java.util.Map<?, ?>) o).entrySet()) {
                if (!first) b.append(','); first = false;
                b.append(q(String.valueOf(e.getKey()))).append(':').append(algoblockJson(e.getValue()));
            }
            return b.append('}').toString();
        }
        return q(o.toString());
    }
"""


def defines_solution(source):
    return bool(re.search(r"\bclass\s+Solution\b", source)) and bool(SIGNATURE.search(source))


def defines_main(source):
    return bool(re.search(r"\bclass\s+Main\b", source)) and bool(re.search(r"static\s+void\s+main\s*\(", source))


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


READER = r"""
    static String algoblockStr(String f) throws Exception { return new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(f)), java.nio.charset.StandardCharsets.UTF_8); }
    static java.util.StringTokenizer algoblockTok(String f) throws Exception { return new java.util.StringTokenizer(algoblockStr(f)); }
    static String[] algoblockStrs(String f) throws Exception { String[] rows = algoblockStr(f).split("\n", -1); String[] out = new String[Integer.parseInt(rows[0])]; System.arraycopy(rows, 1, out, 0, out.length); return out; }
    static String[][] algoblockStrs2(String f) throws Exception { String[] rows = algoblockStr(f).split("\n", -1); String[][] out = new String[Integer.parseInt(rows[0])][]; int at = 1; for (int i = 0; i < out.length; i++) { out[i] = new String[Integer.parseInt(rows[at++])]; for (int j = 0; j < out[i].length; j++) out[i][j] = rows[at++]; } return out; }
    static boolean[][] algoblockBools2(String f) throws Exception { java.util.StringTokenizer t = algoblockTok(f); boolean[][] out = new boolean[Integer.parseInt(t.nextToken())][]; for (int i = 0; i < out.length; i++) { out[i] = new boolean[Integer.parseInt(t.nextToken())]; for (int j = 0; j < out[i].length; j++) out[i][j] = t.nextToken().equals("1"); } return out; }
    static int[] algoblockInts(java.util.StringTokenizer t) { int[] out = new int[Integer.parseInt(t.nextToken())]; for (int i = 0; i < out.length; i++) out[i] = Integer.parseInt(t.nextToken()); return out; }
    static long[] algoblockLongs(java.util.StringTokenizer t) { long[] out = new long[Integer.parseInt(t.nextToken())]; for (int i = 0; i < out.length; i++) out[i] = Long.parseLong(t.nextToken()); return out; }
    static int[] algoblockInts(String f) throws Exception { return algoblockInts(algoblockTok(f)); }
    static long[] algoblockLongs(String f) throws Exception { return algoblockLongs(algoblockTok(f)); }
    static boolean[] algoblockBools(String f) throws Exception { java.util.StringTokenizer t = algoblockTok(f); boolean[] out = new boolean[Integer.parseInt(t.nextToken())]; for (int i = 0; i < out.length; i++) out[i] = t.nextToken().equals("1"); return out; }
    static int[][] algoblockInts2(String f) throws Exception { java.util.StringTokenizer t = algoblockTok(f); int[][] out = new int[Integer.parseInt(t.nextToken())][]; for (int i = 0; i < out.length; i++) out[i] = algoblockInts(t); return out; }
    static long[][] algoblockLongs2(String f) throws Exception { java.util.StringTokenizer t = algoblockTok(f); long[][] out = new long[Integer.parseInt(t.nextToken())][]; for (int i = 0; i < out.length; i++) out[i] = algoblockLongs(t); return out; }
"""


def read_expr(typ, name):
    """큰 인자를 파일에서 읽는 식(tm.file_text가 쓴 모양)."""
    if typ.base == "string":
        return f'algoblockStr{("", "s", "s2")[typ.dims]}("{name}")'
    word = {"int": "Ints", "long": "Longs", "bool": "Bools"}[typ.base]
    return f'algoblock{word}{"2" if typ.dims == 2 else ""}("{name}")'


def harness(source, args, work):
    found = SIGNATURE.search(source)
    params = tm.split_params(found.group(2))
    types = [tm.java_type(re.sub(r"\s+\w+$", "", p.strip())) for p in params]
    cases = []
    for index, values in enumerate(args):
        if len(values) != len(types):
            raise tm.Unsupported(f"{index + 1}번째 케이스 인자 수 {len(values)}개, 선언 {len(types)}개")
        call = ", ".join(tm.argument(tm.java, read_expr, v, t, work, f"case{index}_{n}.txt") for n, (v, t) in enumerate(zip(values, types)))
        cases.append(f"            case {index}: r = s.solution({call}); break;")
    body = "\n".join(cases)
    return (
        "public class FunctionRunner {\n"
        "    public static void main(String[] a) throws Exception {\n"
        "        Solution s = new Solution();\n        Object r;\n"
        "        switch (Integer.parseInt(a[0])) {\n" + body + "\n"
        "            default: throw new IllegalArgumentException(a[0]);\n        }\n"
        "        System.out.println(algoblockJson(r));\n    }\n" + PRINTER + READER + "}\n"
    )


def prepare(mode, source, args, work):
    if mode == "function":
        (work / "Solution.java").write_text(source, encoding="utf-8")
        (work / "FunctionRunner.java").write_text(harness(source, args, work), encoding="utf-8")
        return ["javac", "-encoding", "UTF-8", "Solution.java", "FunctionRunner.java"]
    (work / "Main.java").write_text(source, encoding="utf-8")
    return ["javac", "-encoding", "UTF-8", "Main.java"]


def command(mode, index):
    return ["java", "-Xss256m", "FunctionRunner", str(index)] if mode == "function" else ["java", "-Xss256m", "Main"]
