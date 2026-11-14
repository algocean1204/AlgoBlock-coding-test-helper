"""Go. 함수 모드는 같은 package main에 algoblock_main.go를 더해 solution을 부르고 encoding/json으로 출력한다."""

import re

TOOLS = ("go",)
SAMPLE = {"function": "solution.go", "program": "main.go"}
ENTRY = {"function": "func solution", "program": "func main"}
tm = common = None  # judge.py가 넣는다

SIGNATURE = re.compile(r"func\s+solution\s*\(([^)]*)\)")


def defines_solution(source):
    return bool(SIGNATURE.search(source))


def defines_main(source):
    return bool(re.search(r"\bfunc\s+main\s*\(\s*\)", source))


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


def param_types(text):
    """'a, b int, s string' 처럼 형을 묶어 쓴 것도 푼다."""
    names, types = [], []
    for part in tm.split_params(text):
        pieces = part.split(None, 1)
        names.append(pieces[0])
        if len(pieces) == 2:
            types.extend([pieces[1]] * (len(names) - len(types)))
    if len(types) != len(names):
        raise tm.Unsupported(text)
    return [tm.go_type(t) for t in types]


READER = r"""
func algoblockStr(f string) string { b, _ := algoblockOS.ReadFile(f); return string(b) }
func algoblockStrs(f string) []string { rows := algoblockStrings.Split(algoblockStr(f), "\n"); n, _ := algoblockConv.Atoi(rows[0]); return rows[1 : n+1] }
func algoblockStrs2(f string) [][]string {
	rows := algoblockStrings.Split(algoblockStr(f), "\n")
	n, _ := algoblockConv.Atoi(rows[0])
	at := 1
	out := make([][]string, n)
	for i := range out {
		m, _ := algoblockConv.Atoi(rows[at])
		out[i] = rows[at+1 : at+1+m]
		at += 1 + m
	}
	return out
}
func algoblockBools2(f string) [][]bool {
	nums := algoblockNums2[int](f)
	out := make([][]bool, len(nums))
	for i, row := range nums {
		out[i] = make([]bool, len(row))
		for j, v := range row {
			out[i][j] = v == 1
		}
	}
	return out
}
func algoblockRow[T int | int32 | int64](w []string, at *int) []T {
	n, _ := algoblockConv.Atoi(w[*at])
	*at++
	out := make([]T, n)
	for i := range out {
		v, _ := algoblockConv.ParseInt(w[*at], 10, 64)
		*at++
		out[i] = T(v)
	}
	return out
}
func algoblockNums[T int | int32 | int64](f string) []T { at := 0; return algoblockRow[T](algoblockStrings.Fields(algoblockStr(f)), &at) }
func algoblockNums2[T int | int32 | int64](f string) [][]T {
	w := algoblockStrings.Fields(algoblockStr(f))
	n, _ := algoblockConv.Atoi(w[0])
	at := 1
	out := make([][]T, n)
	for i := range out {
		out[i] = algoblockRow[T](w, &at)
	}
	return out
}
func algoblockBools(f string) []bool { nums := algoblockNums[int](f); out := make([]bool, len(nums)); for i, v := range nums { out[i] = v == 1 }; return out }
"""


def read_expr(typ, name):
    """큰 인자를 파일에서 읽는 식(tm.file_text가 쓴 모양)."""
    if typ.base == "string":
        return f'algoblockStr{("", "s", "s2")[typ.dims]}("{name}")'
    if typ.base == "bool":
        return f'algoblockBools{"2" if typ.dims == 2 else ""}("{name}")'
    element = {"int": "int", "long": "int64"}[typ.base]
    return f'algoblockNums{"2" if typ.dims == 2 else ""}[{element}]("{name}")'


def harness(source, args, work):
    types = param_types(SIGNATURE.search(source).group(1))
    rows = []
    for index, values in enumerate(args):
        if len(values) != len(types):
            raise tm.Unsupported(f"{index + 1}번째 케이스 인자 수 {len(values)}개, 선언 {len(types)}개")
        rows.append(f"\tcase {index}:\n\t\tr = solution(" + ", ".join(tm.argument(tm.go, read_expr, v, t, work, f"case{index}_{n}.txt") for n, (v, t) in enumerate(zip(values, types))) + ")")
    return (
        'package main\n\nimport (\n\talgoblockJSON "encoding/json"\n\talgoblockFmt "fmt"\n\talgoblockOS "os"\n\talgoblockReflect "reflect"\n\talgoblockConv "strconv"\n\talgoblockStrings "strings"\n)\n\n'
        "func main() {\n\tindex, _ := algoblockConv.Atoi(algoblockOS.Args[1])\n\tvar r interface{}\n"
        "\tswitch index {\n" + "\n".join(rows) + "\n\tdefault:\n\t\talgoblockOS.Exit(2)\n\t}\n"
        "\tout, err := algoblockJSON.Marshal(r)\n\tif err != nil {\n\t\talgoblockFmt.Fprintln(algoblockOS.Stderr, err)\n\t\talgoblockOS.Exit(1)\n\t}\n"
        # nil 슬라이스는 null이 아니라 빈 배열로 낸다(Go에서 빈 결과를 nil로 돌려주는 일이 흔하다)
        "\tif v := algoblockReflect.ValueOf(r); v.Kind() == algoblockReflect.Slice && v.IsNil() {\n\t\tout = []byte(\"[]\")\n\t}\n"
        "\talgoblockFmt.Println(string(out))\n}\n" + READER
    )


def without_main(source):
    """함수 모드: 제출 코드의 main은 호출 코드의 main과 겹치므로 이름을 바꾼다(실행되지 않는다)."""
    return re.sub(r"\bfunc\s+main\s*\(\s*\)", "func algoblockUserMain()", source)


def prepare(mode, source, args, work):
    (work / "go.mod").write_text("module algoblockcheck\n\ngo 1.21\n", encoding="utf-8")
    if mode == "function":
        (work / "solution.go").write_text(without_main(source), encoding="utf-8")
        (work / "algoblock_main.go").write_text(harness(source, args, work), encoding="utf-8")
    else:
        (work / "main.go").write_text(source, encoding="utf-8")
    return ["go", "build", "-o", "app", "."]


def command(mode, index):
    return ["./app", str(index)] if mode == "function" else ["./app"]
