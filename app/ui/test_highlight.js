// 문법 색(highlight.js) 시험. 실행: node app/ui/test_highlight.js (틀 없이 assert만)
// 1. 글이 바뀌지 않는다: 기본 풀이 전부에서 토큰의 글을 이으면 원래 코드와 같다
// 2. 언어마다 대표 토큰
// 3. HTML 이스케이프
// 4. macOS 12의 웹뷰(Safari 15쯤)가 모르는 문법을 화면 스크립트에 쓰지 않는다
"use strict";
const fs = require("fs"), path = require("path"), assert = require("assert");
const { tokens, lines, same, LANGS } = require("./highlight.js");

const EXT = { python: "py", javascript: "js", java: "java", cpp: "cpp", rust: "rs" };
assert.deepStrictEqual([...LANGS].sort(), Object.keys(EXT).sort());

// 1. 기본 풀이 전부
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));
const files = walk(path.join(__dirname, "problems"));
let count = 0;
const unhtml = (h) => h.replace(/<[^>]*>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
for (const [lang, ext] of Object.entries(EXT)) {
  const mine = files.filter((f) => path.basename(f) === `solution.${ext}`);
  assert.ok(mine.length > 0, `${lang} 풀이가 없다`);
  for (const f of mine) {
    const code = fs.readFileSync(f, "utf8");
    const got = tokens(code, lang);
    assert.strictEqual(got.map((t) => t[1]).join(""), code, f);
    assert.ok(got.some((t) => t[0] === "k"), `${f}: 키워드가 하나도 없다`);
    const rows = lines(code, lang); // 줄마다의 HTML: 줄 수가 같고, 태그를 걷으면 그 줄의 글이며, 줄마다 span이 닫힌다
    assert.strictEqual(rows.length, code.split("\n").length, f);
    rows.forEach((row, i) => {
      assert.strictEqual(unhtml(row), code.split("\n")[i], `${f}:${i + 1}`);
      assert.strictEqual((row.match(/<span /g) || []).length, (row.match(/<\/span>/g) || []).length, `${f}:${i + 1}`);
    });
    count++;
  }
}
assert.ok(count >= 375, `기본 풀이가 ${count}개뿐이다`);

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
  ["rust", 'fn f<\'a>(x: &\'a str) -> usize { let c = \'x\'; let s = r#"a"b"#; println!("{}", s); if a!=b { 1_000u64 } else { 0 } }', 'k:fn|f:f|t:str|t:usize|k:let|s:\'x\'|k:let|s:r#"a"b"#|b:println!|s:"{}"|k:if|n:1_000u64|k:else|n:0'],
  ["rust", 'let v: Vec<i64> = Vec::new(); let b = b"xy"; let o = Some(x.0); /* c */', 'k:let|t:Vec|t:i64|t:Vec|f:new|k:let|s:b"xy"|k:let|v:Some|n:0|c:/* c */'],
  // 삼중 따옴표 안의 \"""는 문자열을 끝내지 않는다(Python·Java).
  ["python", 's = """a \\""" b"""\nx = 1', 's:"""a \\""" b"""|n:1'],
  ["java", 'String q = """\nx \\""" y"""; int n;', 't:String|s:"""\nx \\""" y"""|t:int'],
  // 정규식 리터럴 안의 백틱이 뒤를 문자열로 물들이지 않는다. 나눗셈은 정규식이 아니다
  ["javascript", 's = t.replace(/`[a/]\\//g, ""); const h = a / 2 / b;\nlet z = 1;', 'f:replace|s:/`[a/]\\//g|s:""|k:const|n:2|k:let|n:1'],
];
let bad = 0;
for (const [lang, code, want] of CASES) {
  assert.strictEqual(tokens(code, lang).map((t) => t[1]).join(""), code, lang);
  const got = tokens(code, lang).filter((t) => t[0]).map((t) => t.join(":")).join("|");
  if (got !== want) { bad++; console.log(`어긋남 ${lang}\n  얻음 ${got}\n  기대 ${want}`); }
}
assert.strictEqual(bad, 0, `대표 토큰 ${bad}개가 어긋났다`);
assert.deepStrictEqual(tokens("a < b", "brainfuck"), [["", "a < b"]]); // 모르는 언어는 본문 그대로
assert.deepStrictEqual(lines("/* a\n<b */ x", "java"), ['<span class="t-c">/* a</span>', '<span class="t-c">&lt;b */</span> x']); // 여러 줄 주석은 줄마다 다시 연다
assert.deepStrictEqual(lines("a<\n", "brainfuck"), ["a&lt;", ""]); // 모르는 언어(색을 끈 때)는 글만

// 3. 사용자의 코드가 innerHTML로 들어간다: &, <, >가 모두 바뀌어 태그가 생기지 않는다
for (const lang of LANGS) {
  const html = lines('x = "<script>alert(1)</script>" // <b>&amp;</b>\n<img src=x onerror=alert(1)> & y', lang).join("\n");
  assert.ok(!/<(?!\/?span[ >])/.test(html), `${lang}: 바꾸지 않은 < 가 있다: ${html}`);
  assert.ok(!/&(?!amp;|lt;|gt;)/.test(html), `${lang}: 바꾸지 않은 & 가 있다`);
}

// 4. 화면 스크립트에 macOS 12 웹뷰가 모르는 문법이 없다(주석은 뺀다). 뒤돌아보기 정규식은 문법 오류라 파일 전체가 죽는다
const UNSUPPORTED = [[/\(\?<[=!]/, "정규식 뒤돌아보기"], [/\.at\(/, "Array.prototype.at"], [/\bObject\.hasOwn\b/, "Object.hasOwn"], [/\.findLast(Index)?\(/, "findLast"], [/\bstructuredClone\(/, "structuredClone"]];
for (const name of ["highlight.js", "app.js"]) {
  const src = tokens(fs.readFileSync(path.join(__dirname, name), "utf8"), "javascript").filter((t) => t[0] !== "c").map((t) => t[1]).join("");
  for (const [re, what] of UNSUPPORTED) assert.ok(!re.test(src), `${name}: ${what}를 쓴다`);
}

// 5. 되돌아가기 폭발이 없다: 치는 중에 생기는 닫지 않은 줄이 화면을 멈추지 않는다(자동 저장되어 다시 열어도 멈춘다)
const ms = (fn) => { const t = process.hrtime.bigint(); fn(); return Number(process.hrtime.bigint() - t) / 1e6; };
// 작은 것부터: 폭발하는 판이면 큰 입력에서 멈추기 전에 여기서 실패한다
const SLOW = [14, 30].flatMap((n) => [["javascript", "f(/" + "[[]".repeat(n), 10], ["javascript", "x = /" + "[a]".repeat(n + 10), 10]]);
const BAD = ['"', "'", "\\", "`", "/*", '"""', "'''", "\\\"", "[", "(/", "r#", 'R"(', "#", "@", "0x", "1.", "${"];
for (const lang of LANGS) for (const bad of BAD) SLOW.push([lang, "x = " + bad.repeat(2000), 50], [lang, ("a(" + bad).repeat(1000), 50]);
for (const [lang, code, limit] of SLOW) {
  tokens(code, lang); // 정규식을 만드는 시간은 빼고 잰다
  const took = ms(() => tokens(code, lang));
  assert.ok(took < limit, `${lang} ${JSON.stringify(code.slice(0, 12))}…(${code.length}자): ${took.toFixed(1)}ms`);
}

// 6. 줄 단위 다시 칠하기: 앞뒤의 같은 줄을 건너뛰고 가운데만 바꿔 넣어도 처음부터 다시 칠한 것과 같다(무작위 고침)
let seed = 1;
const rand = (n) => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
const PIECES = ["\n", '"""', "/*", "*/", "'", '"', "#", "//", "`", "x", "  ", "(", "/", "\\"];
for (const [lang, ext] of Object.entries(EXT)) {
  let code = fs.readFileSync(files.find((f) => path.basename(f) === `solution.${ext}`), "utf8"), shown = lines(code, lang);
  for (let i = 0; i < 300; i++) {
    const at = rand(code.length + 1), cut = rand(4);
    code = code.slice(0, at) + (rand(3) ? PIECES[rand(PIECES.length)] : "") + code.slice(at + cut);
    const rows = lines(code, lang), [head, tail] = same(shown, rows);
    shown = [...shown.slice(0, head), ...rows.slice(head, rows.length - tail), ...shown.slice(shown.length - tail)];
    assert.deepStrictEqual(shown, rows, `${lang} 고침 ${i + 1}`);
  }
}

// 속도(참고): 긴 코드를 칠하는 데 드는 시간
const base = fs.readFileSync(files.find((f) => f.endsWith("solution.py")), "utf8").split("\n");
const speed = [300, 1000, 2000].map((n) => {
  const code = Array.from({ length: n }, (_, i) => base[i % base.length]).join("\n");
  const t = process.hrtime.bigint();
  for (let i = 0; i < 20; i++) lines(code, "python");
  return `${n}줄 ${(Number(process.hrtime.bigint() - t) / 20e6).toFixed(2)}ms`;
});
console.log(`문법 색 시험 통과: 기본 풀이 ${count}개, 대표 ${CASES.length}개 · ${speed.join(", ")}`);
