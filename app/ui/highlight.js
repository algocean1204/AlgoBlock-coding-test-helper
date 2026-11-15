/* 코드 칸의 문법 색. 채점 언어 7개를 한 언어에 정규식 하나로 앞에서부터 훑는다(파서가 아니다: 눈에 도움이 되는 수준).
   글은 바꾸지 않는다: tokens()의 글을 이으면 원래 코드와 같다(test_highlight.js가 기본 풀이 전부로 본다).
   종류: k 키워드, s 문자열, c 주석, n 숫자, v 상수, f 함수 이름, t 형, b 내장. 연산자·괄호·보통 이름은 종류 없이 본문색이다.
   macOS 12의 웹뷰(Safari 15쯤)에서도 돌아야 한다: 정규식에 뒤돌아보기((?<=…), (?<!…))를 쓰지 않는다(문법 오류로 파일 전체가 죽는다).
   브라우저에서는 window.AlgoBlockHighlight, Node에서는 module.exports. */
(function (root) {
  "use strict";
  const W = (s) => new Set(s.split(" "));
  const END = String.raw`(?![\s\S])`; // 글 끝(닫는 표시가 없으면 끝까지)
  const C_COMMENT = String.raw`\/\/[^\n]*|\/\*[\s\S]*?(?:\*\/|${END})`;
  // 한 줄 문자열은 닫는 따옴표나 줄 끝에서 멈춘다(닫지 않아도 아랫줄이 물들지 않는다)
  const DQ = String.raw`"(?:\\.|[^"\\\n])*"?`, SQ = String.raw`'(?:\\.|[^'\\\n])*'?`;
  const CH = String.raw`'(?:\\[^\n][^'\n]{0,9}|[^'\\\n])'`; // 글자 하나('a', '\n', '\''). 닫는 따옴표가 없으면 문자열이 아니다(Rust의 수명 'a)
  const TRIPLE = (q) => `${q}${q}${q}[\\s\\S]*?(?:${q}${q}${q}|${END})`;
  const NUM = String.raw`\b(?:0[xX][\da-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?)\w*|\B\.\d[\d_]*(?:[eE][+-]?\d+)?\w*`;
  const L = {
    python: {
      c: "#[^\\n]*",
      s: String.raw`(?:\b[rRbBfFuU]{1,2})?(?:${TRIPLE('"')}|${TRIPLE("'")}|${DQ}|${SQ})`,
      k: W("and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield"),
      v: W("True False None"),
      b: W("print len range enumerate zip map filter sorted reversed sum min max abs any all int float str bool list dict set tuple frozenset input open isinstance iter next divmod pow round ord chr type super"),
      deco: true,
    },
    javascript: {
      c: C_COMMENT,
      s: "`(?:\\\\[\\s\\S]|[^`\\\\])*`?|" + `${DQ}|${SQ}`,
      k: W("async await break case catch class const continue debugger default delete do else export extends finally for function if import in instanceof let new return static super switch this throw try typeof var void while yield"),
      v: W("true false null undefined NaN Infinity"),
      b: W("console require module exports process parseInt parseFloat isNaN globalThis"),
    },
    java: {
      c: C_COMMENT,
      s: `${TRIPLE('"')}|${DQ}|${CH}`,
      k: W("abstract assert break case catch class const continue default do else enum extends final finally for goto if implements import instanceof interface native new package private protected public record return static strictfp super switch synchronized this throw throws transient try var volatile while yield"),
      t: W("boolean byte char double float int long short void"),
      v: W("true false null"),
      deco: true,
    },
    cpp: {
      c: C_COMMENT,
      s: String.raw`(?:\b(?:u8|[uUL]))?(?:R"(?<rd>[^\s()\\"]{0,16})\([\s\S]*?(?:\)\k<rd>"|${END})|${DQ}|${CH})`,
      k: W("alignas alignof auto break case catch class const constexpr const_cast continue decltype default delete do dynamic_cast else enum explicit export extern for friend goto if inline mutable namespace new noexcept operator private protected public register reinterpret_cast return sizeof static static_cast struct switch template this throw try typedef typeid typename union using virtual volatile while"),
      t: W("bool char char16_t char32_t double float int long short signed unsigned void wchar_t size_t int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t string vector map set pair queue stack deque list array tuple unordered_map unordered_set priority_queue multiset multimap bitset"),
      v: W("true false nullptr NULL"),
      b: W("std cout cin cerr endl"),
      pre: true,
    },
    go: {
      c: C_COMMENT,
      s: "`[^`]*`?|" + `${DQ}|${CH}`,
      k: W("break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var"),
      t: W("int int8 int16 int32 int64 uint uint8 uint16 uint32 uint64 uintptr float32 float64 complex64 complex128 string bool byte rune error any"),
      v: W("true false nil iota"),
      b: W("len cap append make new copy delete panic recover print println close min max clear"),
      capCall: true, // 대문자로 시작해도 뒤에 (가 오면 함수(fmt.Println)
    },
    kotlin: {
      c: C_COMMENT,
      s: `${TRIPLE('"')}|${DQ}|${CH}`,
      k: W("as break by catch class companion const constructor continue data do else enum final finally for fun if import in inner interface internal is lateinit object open operator override package private protected public return sealed super suspend this throw try typealias val var vararg when while"),
      v: W("true false null"),
      b: W("println print listOf mutableListOf arrayOf intArrayOf longArrayOf mapOf mutableMapOf setOf mutableSetOf maxOf minOf repeat readLine readln"),
      deco: true,
    },
    rust: {
      c: C_COMMENT,
      s: String.raw`(?:\bb)?(?:r(?<rh>#*)"[\s\S]*?(?:"\k<rh>|${END})|"(?:\\[\s\S]|[^"\\])*"?|${CH})`,
      k: W("as async await break const continue crate dyn else enum extern fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait type unsafe use where while"),
      t: W("i8 i16 i32 i64 i128 u8 u16 u32 u64 u128 isize usize f32 f64 bool char str"),
      v: W("true false Some None Ok Err"),
      macro: true, // 이름! 은 매크로(println!). != 은 아니다
    },
  };
  const DEF = W("def fn func fun function"), CALL = /[ \t]*\(/y, GAP = /^[ \t]+$/;
  const RX = {};
  function rx(lang) {
    const d = L[lang];
    return RX[lang] || (RX[lang] = new RegExp(
      `(?<c>${d.c})|(?<s>${d.s})|(?<n>${NUM})` +
      (d.pre ? String.raw`|(?<p>^[ \t]*#[ \t]*[a-z]+)(?<ph>[ \t]*<[^>\n]*>)?` : "") + // #include <vector>: 지시어는 키워드, 머리 파일 이름은 문자열
      (d.deco ? String.raw`|(?<d>@[A-Za-z_][\w.]*)` : "") +
      String.raw`|(?<w>[A-Za-z_$][\w$]*${d.macro ? "(?:!(?!=))?" : ""})`, "gm"));
  }
  function kindOf(d, g, call, named) {
    if (g.c !== undefined) return "c";
    if (g.s !== undefined) return "s";
    if (g.n !== undefined) return "n";
    if (g.p !== undefined) return "k";
    if (g.d !== undefined) return "b";
    const w = g.w;
    if (d.k.has(w)) return "k";
    if (d.v && d.v.has(w)) return "v";
    if (d.t && d.t.has(w)) return "t";
    if (d.b && d.b.has(w)) return "b";
    if (w.endsWith("!")) return "b";
    const cap = /^[A-Z]/.test(w);
    if ((named || call) && (d.capCall || !cap)) return "f";
    if (/^[A-Z][A-Z0-9_]*$/.test(w)) return "v"; // 대문자·숫자·밑줄만(N, INF, MAX_N): 상수 이름
    return cap ? "t" : "";
  }
  /** [종류, 글] 목록. 종류 ""는 본문. 글을 이으면 원래 코드와 같다. 모르는 언어는 통째로 본문이다. */
  function tokens(code, lang) {
    const d = L[lang];
    if (!d) return [["", code]];
    const out = [], re = rx(lang);
    let at = 0, m, defEnd = -1;
    re.lastIndex = 0;
    while ((m = re.exec(code))) {
      if (!m[0]) { re.lastIndex++; continue; }
      const end = re.lastIndex;
      CALL.lastIndex = end;
      const named = defEnd >= 0 && GAP.test(code.slice(defEnd, m.index)); // def·fn·func·fun·function 바로 다음 이름
      const kind = kindOf(d, m.groups, CALL.test(code), named);
      defEnd = kind === "k" && DEF.has(m[0]) ? end : -1;
      if (!kind) continue; // 보통 이름은 앞뒤 본문과 한 조각으로
      if (m.index > at) out.push(["", code.slice(at, m.index)]);
      if (m.groups.ph) out.push(["k", m.groups.p], ["s", m.groups.ph]);
      else out.push([kind, m[0]]);
      at = end;
    }
    if (at < code.length) out.push(["", code.slice(at)]);
    return out;
  }
  const esc = (s) => s.replace(/[&<>]/g, (ch) => (ch === "&" ? "&amp;" : ch === "<" ? "&lt;" : "&gt;"));
  /** innerHTML에 넣을 글. 사용자의 코드가 그대로 들어오는 자리라 &, <, >를 모두 바꾼다. */
  const highlight = (code, lang) => tokens(code, lang).map(([k, text]) => (k ? `<span class="t-${k}">${esc(text)}</span>` : esc(text))).join("");
  const api = { tokens, highlight, LANGS: Object.keys(L) };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AlgoBlockHighlight = api;
})(typeof window !== "undefined" ? window : globalThis);
