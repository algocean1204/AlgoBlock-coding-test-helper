"""Rust. 함수 모드는 algoblock_main.rs에서 include!("solution.rs")로 제출 코드를 같은 모듈에 넣고 solution을 부른다(pub 없어도 된다)."""

import re

TOOLS = ("rustc",)
SAMPLE = {"function": "solution.rs", "program": "main.rs"}
ENTRY = {"function": "fn solution", "program": "fn main"}
tm = common = None  # judge.py가 넣는다

SIGNATURE = re.compile(r"fn\s+solution\s*\(([^)]*)\)")

PRINTER = r'''
trait AlgoblockJson { fn algoblock_json(&self) -> String; }
macro_rules! algoblock_num { ($($t:ty),*) => { $(impl AlgoblockJson for $t { fn algoblock_json(&self) -> String { self.to_string() } })* } }
algoblock_num!(i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize);
impl AlgoblockJson for bool { fn algoblock_json(&self) -> String { self.to_string() } }
impl AlgoblockJson for f64 { fn algoblock_json(&self) -> String { if self.fract() == 0.0 && self.abs() < 1e15 { format!("{:.1}", self) } else { format!("{}", self) } } }
impl AlgoblockJson for f32 { fn algoblock_json(&self) -> String { (*self as f64).algoblock_json() } }
fn algoblock_quote(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""), '\\' => out.push_str("\\\\"), '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"), '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}
impl AlgoblockJson for String { fn algoblock_json(&self) -> String { algoblock_quote(self) } }
impl AlgoblockJson for &str { fn algoblock_json(&self) -> String { algoblock_quote(self) } }
impl AlgoblockJson for char { fn algoblock_json(&self) -> String { algoblock_quote(&self.to_string()) } }
impl<T: AlgoblockJson> AlgoblockJson for Vec<T> { fn algoblock_json(&self) -> String { format!("[{}]", self.iter().map(|x| x.algoblock_json()).collect::<Vec<_>>().join(",")) } }
impl<T: AlgoblockJson, const N: usize> AlgoblockJson for [T; N] { fn algoblock_json(&self) -> String { format!("[{}]", self.iter().map(|x| x.algoblock_json()).collect::<Vec<_>>().join(",")) } }
'''


def defines_solution(source):
    return bool(SIGNATURE.search(source))


def defines_main(source):
    return bool(re.search(r"\bfn\s+main\s*\(\s*\)", source))


def has_entry(mode, source):
    return defines_solution(source) if mode == "function" else defines_main(source)


READER = r"""
fn algoblock_str(f: &str) -> String { std::fs::read_to_string(f).unwrap() }
fn algoblock_leak(s: String) -> &'static str { Box::leak(s.into_boxed_str()) }
fn algoblock_strs(f: &str) -> Vec<String> { let s = algoblock_str(f); let mut rows = s.split('\n'); let n: usize = rows.next().unwrap().parse().unwrap(); rows.take(n).map(String::from).collect() }
fn algoblock_strs_ref(f: &str) -> Vec<&'static str> { algoblock_strs(f).into_iter().map(algoblock_leak).collect() }
fn algoblock_strs2(f: &str) -> Vec<Vec<String>> { let s = algoblock_str(f); let mut rows = s.split('\n'); let n: usize = rows.next().unwrap().parse().unwrap(); (0..n).map(|_| { let m: usize = rows.next().unwrap().parse().unwrap(); (0..m).map(|_| String::from(rows.next().unwrap())).collect() }).collect() }
fn algoblock_strs2_ref(f: &str) -> Vec<Vec<&'static str>> { algoblock_strs2(f).into_iter().map(|row| row.into_iter().map(algoblock_leak).collect()).collect() }
fn algoblock_bools2(f: &str) -> Vec<Vec<bool>> { algoblock_nums2::<u8>(f).into_iter().map(|row| row.into_iter().map(|v| v == 1).collect()).collect() }
fn algoblock_row<'a, T: std::str::FromStr>(it: &mut impl Iterator<Item = &'a str>) -> Vec<T> where T::Err: std::fmt::Debug { let n: usize = it.next().unwrap().parse().unwrap(); (0..n).map(|_| it.next().unwrap().parse().unwrap()).collect() }
fn algoblock_nums<T: std::str::FromStr>(f: &str) -> Vec<T> where T::Err: std::fmt::Debug { let s = algoblock_str(f); algoblock_row(&mut s.split_ascii_whitespace()) }
fn algoblock_nums2<T: std::str::FromStr>(f: &str) -> Vec<Vec<T>> where T::Err: std::fmt::Debug { let s = algoblock_str(f); let mut it = s.split_ascii_whitespace(); let n: usize = it.next().unwrap().parse().unwrap(); (0..n).map(|_| algoblock_row(&mut it)).collect() }
fn algoblock_bools(f: &str) -> Vec<bool> { algoblock_nums::<u8>(f).into_iter().map(|v| v == 1).collect() }
"""


def read_expr(typ, name):
    """큰 인자를 파일에서 읽는 식(tm.file_text가 쓴 모양)."""
    if typ.base == "string":
        if typ.dims:
            return f'algoblock_strs{"2" if typ.dims == 2 else ""}{"_ref" if typ.ref_str else ""}("{name}")'
        return f'algoblock_leak(algoblock_str("{name}"))' if typ.ref_str else f'algoblock_str("{name}")'
    if typ.base == "bool":
        return f'algoblock_bools{"2" if typ.dims == 2 else ""}("{name}")'
    native = typ.native or {"int": "i32", "long": "i64"}[typ.base]
    return f'algoblock_nums{"2" if typ.dims == 2 else ""}::<{native}>("{name}")'


def harness(source, args, work):
    params = tm.split_params(SIGNATURE.search(source).group(1))
    types = [tm.rust_type(p.split(":", 1)[1]) for p in params]
    rows = []
    for index, values in enumerate(args):
        if len(values) != len(types):
            raise tm.Unsupported(f"{index + 1}번째 케이스 인자 수 {len(values)}개, 선언 {len(types)}개")
        rows.append(f"        {index} => solution(" + ", ".join(tm.argument(tm.rust, read_expr, v, t, work, f"case{index}_{n}.txt") for n, (v, t) in enumerate(zip(values, types))) + ").algoblock_json(),")
    return (
        '#![allow(dead_code, unused_imports, unused_variables, unused_mut, non_snake_case)]\ninclude!("solution.rs");\n' + PRINTER + READER +
        "fn main() {\n    let index: usize = std::env::args().nth(1).unwrap().parse().unwrap();\n    let out = match index {\n" +
        "\n".join(rows) + "\n        _ => std::process::exit(2),\n    };\n    println!(\"{}\", out);\n}\n"
    )


def without_main(source):
    """함수 모드: 제출 코드의 main은 호출 코드의 main과 겹치므로 이름을 바꾼다(실행되지 않는다)."""
    return re.sub(r"\bfn\s+main\s*\(\s*\)", "fn algoblock_user_main()", source)


def prepare(mode, source, args, work):
    if mode == "function":
        (work / "solution.rs").write_text(without_main(source), encoding="utf-8")
        (work / "algoblock_main.rs").write_text(harness(source, args, work), encoding="utf-8")
        return ["rustc", "--edition", "2021", "-O", "algoblock_main.rs", "-o", "app"]
    (work / "main.rs").write_text(source, encoding="utf-8")
    return ["rustc", "--edition", "2021", "-O", "main.rs", "-o", "app"]


def command(mode, index):
    return ["./app", str(index)] if mode == "function" else ["./app"]
