// 문법 색(highlight.js) 시험. 실행: node app/ui/test_highlight.js (틀 없이 assert만)
// 1. 글이 바뀌지 않는다: 기본 풀이 전부에서 토큰의 글을 이으면 원래 코드와 같다
// 2. 언어마다 대표 토큰
// 3. HTML 이스케이프
// 4. macOS 12의 웹뷰(Safari 15쯤)가 모르는 문법을 화면 스크립트에 쓰지 않는다
"use strict";
const fs = require("fs"), path = require("path"), assert = require("assert");
const { tokens, highlight, LANGS } = require("./highlight.js");

const EXT = { python: "py", javascript: "js", java: "java", cpp: "cpp", go: "go", kotlin: "kt", rust: "rs" };
assert.deepStrictEqual([...LANGS].sort(), Object.keys(EXT).sort());

// 1. 기본 풀이 전부
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));
const files = walk(path.join(__dirname, "problems"));
let count = 0;
for (const [lang, ext] of Object.entries(EXT)) {
  const mine = files.filter((f) => path.basename(f) === `solution.${ext}`);
  assert.ok(mine.length > 0, `${lang} 풀이가 없다`);
  for (const f of mine) {
    const code = fs.readFileSync(f, "utf8");
    const got = tokens(code, lang);
    assert.strictEqual(got.map((t) => t[1]).join(""), code, f);
    assert.ok(got.some((t) => t[0] === "k"), `${f}: 키워드가 하나도 없다`);
    count++;
  }
}
assert.ok(count >= 500, `기본 풀이가 ${count}개뿐이다`);

// 2. 대표 토큰: 종류가 있는 토큰만 '종류:글'로 잇는다
const CASES = [
  ["python", 'x = f"{a}" # c "q"\ns = """a\nb""" + r\'\\d\'\nif x is None: return 0x1F', `s:f"{a}"|c:# c "q"|s:"""a\nb"""|s:r'\\d'|k:if|k:is|v:None|k:return|n:0x1F`],
  ["python", "N, M = map(int, input().split())\n@lru_cache(None)\ndef solve(a):\n    s = 'it\\'s' + rb'x'\n    return a.count(1.5e3)", "v:N|v:M|b:map|b:int|b:input|f:split|b:@lru_cache|v:None|k:def|f:solve|s:'it\\'s'|s:rb'x'|k:return|f:count|n:1.5e3"],
  ["python", "s = 'open\nt = '''여러\n줄", "s:'open|s:'''여러\n줄"], // 닫지 않은 한 줄 문자열은 줄 끝에서, 여러 줄 문자열은 글 끝까지
  ["javascript", "const s = `a ${b}\n c`; // x\nfoo(1e3); let A = new Map(); function bar(x) { return 10n; }", "k:const|s:`a ${b}\n c`|c:// x|f:foo|n:1e3|k:let|v:A|k:new|t:Map|k:function|f:bar|k:return|n:10n"],
  ["javascript", "/* a\n * b */ console.log(\"q\\\"\", 'x', null);", 'c:/* a\n * b */|b:console|f:log|s:"q\\""|s:\'x\'|v:null'],
  ["java", 'class A { @Override public int f() { String s = "a\\"b"; char c = \'c\', d = \'\\\'\'; return null; } }', `k:class|v:A|b:@Override|k:public|t:int|f:f|t:String|s:"a\\"b"|t:char|s:'c'|s:'\\''|k:return|v:null`],
  ["java", 'String t = """\n  x\n  """; long n = 1_000_000_007L; System.out.println(Math.max(n, 2.5f));', 't:String|s:"""\n  x\n  """|t:long|n:1_000_000_007L|t:System|f:println|t:Math|f:max|n:2.5f'],
  ["cpp", '#include <vector>\n#define MAXN 100\nauto s = R"x(a"b)x"; char c = \'"\'; /* a\n b */ vector<int> v; std::cout << u8"x" << endl;', 'k:#include|s: <vector>|k:#define|v:MAXN|n:100|k:auto|s:R"x(a"b)x"|t:char|s:\'"\'|c:/* a\n b */|t:vector|t:int|b:std|b:cout|s:u8"x"|b:endl'],
  ["cpp", '#include "a.h"\nlong long f(unsigned x) { return x >> 1; }', 'k:#include|s:"a.h"|t:long|t:long|f:f|t:unsigned|k:return|n:1'],
  ["go", "func (r *T) Name() int { s := `a\nb`; fmt.Println(int64(3)); var x []string = nil; return len(s) }", "k:func|v:T|f:Name|t:int|s:`a\nb`|f:Println|t:int64|n:3|k:var|t:string|v:nil|k:return|b:len"],
  ["kotlin", 'fun f(a: Int): String { val s = """x\ny"""; return "a$s" }\nfun <T> g() = listOf(1L)', 'k:fun|f:f|t:Int|t:String|k:val|s:"""x\ny"""|k:return|s:"a$s"|k:fun|v:T|f:g|b:listOf|n:1L'],
  ["rust", 'fn f<\'a>(x: &\'a str) -> usize { let c = \'x\'; let s = r#"a"b"#; println!("{}", s); if a!=b { 1_000u64 } else { 0 } }', 'k:fn|f:f|t:str|t:usize|k:let|s:\'x\'|k:let|s:r#"a"b"#|b:println!|s:"{}"|k:if|n:1_000u64|k:else|n:0'],
  ["rust", 'let v: Vec<i64> = Vec::new(); let b = b"xy"; let o = Some(x.0); /* c */', 'k:let|t:Vec|t:i64|t:Vec|f:new|k:let|s:b"xy"|k:let|v:Some|n:0|c:/* c */'],
];
let bad = 0;
for (const [lang, code, want] of CASES) {
  assert.strictEqual(tokens(code, lang).map((t) => t[1]).join(""), code, lang);
  const got = tokens(code, lang).filter((t) => t[0]).map((t) => t.join(":")).join("|");
  if (got !== want) { bad++; console.log(`어긋남 ${lang}\n  얻음 ${got}\n  기대 ${want}`); }
}
assert.strictEqual(bad, 0, `대표 토큰 ${bad}개가 어긋났다`);
assert.deepStrictEqual(tokens("a < b", "brainfuck"), [["", "a < b"]]); // 모르는 언어는 본문 그대로

// 3. 사용자의 코드가 innerHTML로 들어간다: &, <, >가 모두 바뀌어 태그가 생기지 않는다
for (const lang of LANGS) {
  const html = highlight('x = "<script>alert(1)</script>" // <b>&amp;</b>\n<img src=x onerror=alert(1)> & y', lang);
  assert.ok(!/<(?!\/?span[ >])/.test(html), `${lang}: 바꾸지 않은 < 가 있다: ${html}`);
  assert.ok(!/&(?!amp;|lt;|gt;)/.test(html), `${lang}: 바꾸지 않은 & 가 있다`);
}

// 4. 화면 스크립트에 macOS 12 웹뷰가 모르는 문법이 없다(주석은 뺀다). 뒤돌아보기 정규식은 문법 오류라 파일 전체가 죽는다
const UNSUPPORTED = [[/\(\?<[=!]/, "정규식 뒤돌아보기"], [/\.at\(/, "Array.prototype.at"], [/\bObject\.hasOwn\b/, "Object.hasOwn"], [/\.findLast(Index)?\(/, "findLast"], [/\bstructuredClone\(/, "structuredClone"]];
for (const name of ["highlight.js", "app.js"]) {
  const src = tokens(fs.readFileSync(path.join(__dirname, name), "utf8"), "javascript").filter((t) => t[0] !== "c").map((t) => t[1]).join("");
  for (const [re, what] of UNSUPPORTED) assert.ok(!re.test(src), `${name}: ${what}를 쓴다`);
}

// 속도(참고): 긴 코드를 칠하는 데 드는 시간
const base = fs.readFileSync(files.find((f) => f.endsWith("solution.py")), "utf8").split("\n");
const speed = [300, 1000, 2000].map((n) => {
  const code = Array.from({ length: n }, (_, i) => base[i % base.length]).join("\n");
  const t = process.hrtime.bigint();
  for (let i = 0; i < 20; i++) highlight(code, "python");
  return `${n}줄 ${(Number(process.hrtime.bigint() - t) / 20e6).toFixed(2)}ms`;
});
console.log(`문법 색 시험 통과: 기본 풀이 ${count}개, 대표 ${CASES.length}개 · ${speed.join(", ")}`);
