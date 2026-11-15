"use strict";
/* AlgoBlock 화면. 틀: 상태(S) → 그리기(render*) → 동작(서버 요청) → 다시 그리기.
   입력 칸은 누를 때 .value를 읽는다(도구가 값을 직접 넣고 단추를 눌러도 된다). 알림창(alert)은 쓰지 않는다. */

const $ = (id) => document.getElementById(id);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ico = (name) => `<svg class="ico" aria-hidden="true"><use href="#${name}"/></svg>`;

// 블록 종류: 이름과 한 줄 뜻(사용자가 스스로 묻는 순서의 낱말)
const KIND = {
  var_from_problem: ["문제에서 바로 오는 변수", "문제 글에 이미 나와 있는 값에 이름을 붙이는 자리"],
  var_during: ["풀이 중에 만드는 변수", "풀다 보니 새로 필요해진 값을 담아 두는 자리"],
  loop: ["반복", "같은 일을 여러 번 되풀이하는 자리"],
  condition: ["조건", "'이럴 때만'을 가려내는 자리"],
  branch: ["분기", "경우에 따라 다른 길로 갈라지는 자리"],
};
const KIND_BY_LABEL = Object.fromEntries(Object.entries(KIND).map(([key, [label]]) => [label, key]));
const NEXT_BLOCK = /^다음은 '([^']+)' 블[록럭]이에요\./; // 새 블록의 첫 말은 종류를 알리며 시작한다
const LANG = { python: "Python", java: "Java", javascript: "JavaScript", cpp: "C++", go: "Go", kotlin: "Kotlin", rust: "Rust" };
const TOOL = { python: "Python 3", java: "JDK(javac와 java)", javascript: "Node.js", cpp: "g++ 또는 clang++", go: "Go", kotlin: "Kotlin 컴파일러(kotlinc)와 Java", rust: "Rust(rustc)" };
// 푸는 방식 셋(오른쪽 칸 '어떻게 풀까요?'). 엔진의 이름은 solo·guide(가이드)·chair(생각하는 의자)
const WAYS = {
  solo: ["혼자 풀기", "튜터 없이 풀어요. 막히면 힌트를 하나씩 볼 수 있어요."],
  guide: ["튜터와 차례로", "튜터가 풀이를 블록으로 나눠 하나씩 열어 줘요."],
  chair: ["튜터의 질문으로", "튜터는 답을 주지 않고 질문만 해요. 풀이의 블록을 스스로 찾아요."],
};
const START = {
  chair: ["튜터의 질문으로", "튜터가 질문을 하나씩 던져요. 답을 알려 주지 않고, 풀이의 블록을 스스로 찾도록 이끌어요.", "첫 질문 받기", "튜터가 문제를 읽고 첫 질문을 준비하는 중…"],
  guide: ["튜터와 차례로", "블록 이름을 먼저 보여 주고, 그 블록의 빈칸을 채우도록 이끌어요.", "첫 블록 열기", "튜터가 문제를 읽고 첫 블록을 준비하는 중…"],
  explain: ["튜터의 해설", "튜터가 풀이 전체를 순서대로 설명해요. 스스로 찾아보고 싶다면 ‘튜터의 질문으로’를 먼저 해 보세요.", "해설 받기", "해설을 쓰는 중…"],
};
/* 색 이름표(7번): 단계 1~5, 주제 다섯 갈래, 쓰는 방법(태그. 색 없음), 검증. 색만으로 뜻을 전하지 않게 글자와 같이 쓴다 */
const GROUP = { hash: "ds", stack_queue: "ds", heap: "ds", brute_force: "search", dfs: "search", bfs: "search", binary_search: "search",
  graph: "graph", dijkstra: "graph", greedy: "design", dp: "design", two_pointer: "design", sort: "impl", simulation: "impl", implementation: "impl" };
const GROUP_NAME = { ds: "자료구조", search: "탐색", graph: "그래프", design: "설계", impl: "구현" };
const lvBadge = (n, guess) => (n ? `<span class="lvb l${n}"${guess ? ' title="문제 글을 보고 어림한 단계예요"' : ""}>${n}단계${guess ? " · 어림" : ""}</span>` : "");
const themeChip = (key, name) => (name ? `<span class="theme-chip g-${GROUP[key] || "none"}"${GROUP[key] ? ` title="${GROUP_NAME[GROUP[key]]} 갈래"` : ""}>${esc(name)}</span>` : "");
const tagChips = (tags) => (tags || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("");
const VERIFIED = { all: ["ok", "검증됨"], examples: ["mid", "예시만"], none: ["warn", "검증 못 함"] };
const verifiedBadge = (p) => (VERIFIED[p.verified] ? `<span class="vbadge ${VERIFIED[p.verified][0]}" title="${esc(p.verified_name)}"><i aria-hidden="true"></i>${VERIFIED[p.verified][1]}</span>` : "");
const MANY_HEAD = "예시와 다른 답이에요 — 맞는지 가릴 수 없어요"; // 답이 여럿일 수 있는 문제에서 값만 달랐다(틀렸다고 단정하지 않는다)
const CASE_STATE = { passed: "통과", failed: "답이 달라요", runtime_error: "실행 중 오류", timeout: "시간 초과", skipped: "돌리지 않음", output_limit: "출력이 너무 많아요", memory_limit: "메모리를 너무 많이 썼어요" };
const JUDGE_STATE = {
  entry_missing: ["solution 함수를 찾지 못했어요", "함수 이름과 인자를 시작 코드와 같게 써 주세요."],
  undecided: ["채점할 함수를 찾지 못했어요", "solution이라는 이름의 함수 하나에 풀이를 담아 주세요."],
  toolchain_missing: ["이 기기에 이 언어를 실행할 도구가 없어요", ""],
  no_cases: ["채점할 테스트 케이스가 없어요", ""],
  bad_case: ["테스트 케이스를 읽지 못했어요", "넣을 값이 대괄호로 감싼 목록인지 확인해 주세요."],
  unsupported_signature: ["이 함수 모양은 채점할 수 없어요", "solution 함수의 인자와 형을 시작 코드 그대로 두었는지 확인해 주세요."],
  compile_error: ["컴파일 오류가 났어요", ""], // Python·JavaScript는 컴파일하지 않으니 '문법 오류'(judgeFail)
  timeout: ["시간 안에 끝나지 않았어요", ""],
};
const JUDGE_PROGRAM = { entry_missing: ["프로그램의 시작점을 찾지 못했어요", "시작 코드처럼 main(Java는 public class Main 안의 main)에서 표준 입력을 읽어 주세요."] }; // 표준 입출력 문제에서 다른 말을 쓰는 것
const program = () => !!(S.problem && S.problem.mode === "program"); // 지금 문제가 표준 입출력(프로그램 방식)인가
// 코드가 어느 언어처럼 보이는가(고른 언어와 다르면 알린다). 앞에서부터 처음 맞는 것. C++의 class Solution { public: 은 #include가 없으면 Java로 보일 수 있다
const LOOKS = [["cpp", /#include/], ["kotlin", /\bfun solution\b/], ["go", /\bfunc solution\b/], ["rust", /\bfn solution\b/], ["python", /\bdef solution\b/], ["javascript", /\bfunction solution\b/], ["java", /\bclass Solution\b[\s\S]*\bpublic\b/]];
const looksLike = (code) => (LOOKS.find(([, re]) => re.test(code)) || [null])[0];
const ERR = {
  llm_timeout: "튜터 응답이 너무 오래 걸려 멈췄어요. 한 번 더 보내 주세요.",
  llm_not_configured: "AI가 연결되어 있지 않아요. 오른쪽 위 ‘연결’에서 연결해 주세요.",
  llm_failed: "튜터가 답을 만들지 못했어요. 잠시 뒤 다시 보내 주세요. 계속되면 ‘연결’에서 연결 상태를 확인해 주세요.",
  file_missing: "필요한 파일을 찾지 못했어요. 앱을 닫았다가 다시 열어 주세요.",
  invalid_output: "튜터의 답이 규칙에 맞지 않아 보여 주지 않았어요. 한 번 더 보내 주세요.",
  already_started: "이미 시작한 대화예요.",
  not_submitted: "코드를 한 번 제출한 뒤에 피드백을 받을 수 있어요.",
  network: "앱과 연결이 끊겼어요. 앱을 닫았다가 다시 열어 주세요.",
};

const S = {
  view: "", pid: null, problem: null, session: null, hasFeedback: false,
  mode: null, // 오른쪽 칸: null(아직 고르지 않음), solo, guide, chair, explain(튜터의 해설)
  choosing: false, // '방식 바꾸기'로 고르는 중
  soloOpen: null, // 혼자 풀기에서 펼친 칸: null(접힘), hint, sol
  talk: "chair", // 블록 이름을 어느 대화 기준으로 볼지(해설을 보는 동안에도 직전 대화 기준)
  codeTab: "direct",
  blockCode: {}, // 블록 id → {code, by: "me" | "tutor"}
  result: null, // 마지막 채점 결과 또는 {alert: 알림}. 예시 실행이면 run: true, 직접 입력이면 own: true(서버의 error는 오류 글이라 알림과 이름을 나눈다)
  solo: null, // 혼자 풀기: {shown: 본 힌트들, seen, total, sol: 해설, ask: 포기 확인 중, note}
  langWant: null, // 바꾸려는 언어(확인을 기다리는 중)
  codeAsk: null, // 코드 칸 확인을 기다리는 일: restore(체크포인트로 되돌리기), clear(초기화), pull(블록 코드 가져오기로 바꾸기)
  fillAsk: null, // '이 블록 채우기'로 적은 코드를 바꿀지 묻는 블록 id
  casesOpen: null, // 케이스 목록을 사용자가 펼쳤는지(null이면 기본값)
  quote: null, // 꼬리질문을 열어 둔 튜터 말 id
  sending: null, // 보내는 중인 내 말 {where, text}
  debug: null, // {open, messages, line, code, passed, note}
  note: {}, // 자리별 알림 {chat, start, blocks}
  codeNote: "",
  fb: null, wantFeedback: false,
  busy: null, // {label, where, t0}
};

/* ── 서버 ── */
let leaving = false; // 창을 닫는 중이면 저장 요청이 끊기지 않게 한다
const MODEL_PATHS = ["/api/turn", "/api/followup", "/api/fill", "/api/explain", "/api/feedback", "/api/debug", "/api/problems/read"]; // 모델을 부를 수 있는 요청
let keyBad = false; // 모델 키가 맞지 않다는 답을 받았다(다음 모델 요청이 성공하거나 키를 다시 넣으면 걷는다)
async function api(path, body) {
  try {
    const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}), keepalive: leaving });
    const data = await r.json();
    const out = r.ok ? { ok: true, data } : { ok: false, error: data.detail || { code: "unknown", message: "" } };
    if (out.ok ? MODEL_PATHS.includes(path) || ["/api/key", "/api/key/delete"].includes(path) : out.error.code === "llm_auth_failed") setKeyBad(!out.ok);
    return out;
  } catch (e) {
    return { ok: false, error: { code: "network", message: "" } };
  }
}

/** 머리글의 연결 표시: 키가 맞지 않으면 경고색 '키 확인 필요'. */
function setKeyBad(bad) {
  if (keyBad === bad) return;
  keyBad = bad;
  if (ACCOUNTS) renderAccounts(ACCOUNTS);
}

function errorNote(error) {
  const known = ERR[error.code];
  const text = known || error.message || "알 수 없는 오류가 났어요. 다시 해 보세요.";
  return { type: "error", text, conn: error.code === "llm_not_configured" || error.code === "llm_auth_failed" }; // 키가 틀렸으면 연결 창으로 가는 단추
}

const noteHtml = (n) => !n ? "" : `<div class="note ${n.type || ""}" role="${n.type === "error" ? "alert" : "status"}"><span>${esc(n.text)}</span>${n.conn ? '<button type="button" class="btn small" id="note-conn">연결하기</button>' : ""}${n.again ? '<button type="button" class="btn small" id="prep-again" data-model>다시 준비</button>' : ""}</div>`;
const PREP_FAILED = { type: "error", text: "튜터가 풀이 순서를 준비하지 못했어요.", again: true }; // 보낸 것이 없으니 '한 번 더 보내 주세요'라고 하지 않는다
const say = (text) => { $("status").textContent = text || ""; };
let carried = ""; // 다음 화면에서 보여 줄 상태 문구(화면을 옮기면 상태 문구를 지우므로, 옮기며 남길 말은 여기에)
const sayNext = (text) => { carried = text; };

/* ── 기다림: 무엇을 하는지와 지난 초를 보여 주고, 모델을 부르는 단추를 잠근다 ── */
let ticker = null;
const secs = () => (S.busy ? Math.round((Date.now() - S.busy.t0) / 1000) : 0);
const since = (t0) => Math.round((Date.now() - (t0 || Date.now())) / 1000);
const LATE = "조금 더 걸리고 있어요.";
const late = (n, text) => (n > 30 ? LATE : text); // 걸린다고 말한 시간(30초)을 넘기면 말을 바꾼다
setInterval(() => {
  document.querySelectorAll("[data-since]").forEach((el) => { el.textContent = `${since(Number(el.dataset.since))}초`; }); // 기다림 밖의 진행 줄(튜터 준비)도 초를 센다
  document.querySelectorAll("[data-slow]").forEach((el) => { el.textContent = secs() > 10 ? ` · ${el.dataset.slow}` : ""; });
  document.querySelectorAll("[data-late]").forEach((el) => { el.textContent = late(parseInt(el.parentElement.querySelector(".secs").textContent, 10) || 0, el.dataset.late); });
}, 1000);

function applyBusy() {
  document.querySelectorAll("[data-model]").forEach((el) => { el.disabled = !!S.busy; });
  if (S.view === "code" && noTool()) $("run").disabled = $("submit").disabled = $("run-own-go").disabled = true; // 이 기기에 언어 도구가 없으면 실행·제출을 못 한다
  $("timer").textContent = S.busy ? `${secs()}초` : "";
  document.querySelectorAll("[data-secs]").forEach((el) => { el.textContent = `${secs()}초`; });
}

async function work(label, where, fn, slow) { // slow: 10초를 넘기면 덧붙일 말(모델이 아니라 코드를 돌리는 기다림)
  if (S.busy) return null;
  S.busy = { label, where, t0: Date.now(), slow, pid: S.pid }; // pid: 이 기다림을 시작한 문제(다른 문제 화면에서 진행 글을 그 문제의 것으로 보이지 않게)
  say(label);
  render();
  ticker = setInterval(applyBusy, 1000);
  try {
    return await fn();
  } finally {
    clearInterval(ticker);
    S.busy = null;
    S.sending = null;
    render();
  }
}

const DOTS = '<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>';
const waitLine = (where) => (S.busy && S.busy.where === where // 문구가 걸리는 시간을 말하면(…걸려요) 따로 붙이지 않는다
  ? `${DOTS}<span>${esc(S.busy.label)} <span class="secs" data-secs>${secs()}초</span>${S.busy.slow ? `<span data-slow="${esc(S.busy.slow)}"></span>` : /걸려요$/.test(S.busy.label) ? "" : " · 보통 5~25초 걸려요"}</span>` : "");
const pending = (where) => (S.busy && S.busy.where === where ? `<div class="msg tutor pending"><span class="who">튜터</span><div class="bubble">${waitLine(where)}</div></div>` : "");

/* ── 글 꾸미기: 코드 울타리, 표(| a | b |), 목록(- ), 소제목, `코드`, **굵게**, 표준 입출력 문제의 예제 구역 ── */
const HEADING = /^(문제 설명|제한 ?사항|입출력 예( 설명)?|입출력 예 ?#\d+|입력|출력|예시)$/;
// 예제 구역의 머리(서버 sample_cases와 같은 규칙): 머리 다음부터 다음 머리나 빈 줄 둘 전까지가 그 예제의 글이다
const SAMPLE_HEAD = /^(?:#+\s*)?(예제\s*입력|입력\s*예|sample\s+input|예제\s*출력|출력\s*예|sample\s+output)\s*(\d+)\s*(?:복사)?\s*:?$/i;
const inline = (t) => esc(t).replace(/`([^`\n]+)`/g, "<code>$1</code>").replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");

/** program: 표준 입출력 문제. 예제 구역은 글 그대로 <pre>에 담고, 같은 번호의 입력·출력은 두 칸으로 나란히 둔다. */
// 탭·공백으로 나눈 입출력 예 표(서버 table_cases·flat_table과 같은 규칙의 가장 작은 판정): 머리 줄의 마지막 칸이 결과 낱말이고 뒤 줄들의 칸 수가 맞을 때만 표다
const RESULT_HEADS = new Set(["result", "return", "answer", "결과", "반환", "출력"]);
const tabCells = (line) => line.trim().split(/\t|\s{2,}/).filter((cell) => cell.trim());
/** 칸 구분이 공백 하나로 접힌 표 한 줄('[1, 2, 3] 5 "a b"')의 값들. 값(수, 따옴표 글, 괄호로 묶은 것, 참·거짓·null)이 아닌 것이 있으면 null. */
function flatCells(line) {
  const out = [], row = line.trim();
  let at = 0;
  while (at < row.length) {
    let end = at, depth = 0, quote = "";
    do {
      const c = row[end];
      if (quote) { if (c === "\\") end += 1; else if (c === quote) quote = ""; }
      else if (c === '"' || c === "'") quote = c;
      else if ("[{".includes(c)) depth += 1;
      else if ("]}".includes(c)) depth -= 1;
      end += 1;
    } while (end < row.length && (quote || depth > 0 || !/\s/.test(row[end])));
    const cell = row.slice(at, end);
    if (quote || depth || !(/^["'[{]/.test(cell) || /^-?\d+(\.\d+)?([eE][-+]?\d+)?$|^(true|false|null|True|False|None)$/.test(cell))) return null;
    out.push(cell);
    at = end;
    while (at < row.length && /\s/.test(row[at])) at += 1;
  }
  return out;
}
/** 글 안의 탭·공백 표를 마크다운 표 줄(| a | b |)로 바꾼다. 마크다운 표는 그대로. */
function plainTables(text) {
  const lines = text.split("\n");
  for (let at = 0; at < lines.length; at += 1) {
    if (lines[at].trim().startsWith("|")) continue;
    const tabbed = tabCells(lines[at]), cells = tabbed.length >= 2 ? tabbed : lines[at].trim().split(/\s+/), read = tabbed.length >= 2 ? tabCells : flatCells;
    if (cells.length < 2 || !RESULT_HEADS.has(cells[cells.length - 1].replace(/[`* ]/g, "").toLowerCase())) continue;
    const rows = [];
    let end = at + 1;
    for (; end < lines.length; end += 1) {
      if (!lines[end].trim()) { if (rows.length) break; continue; }
      const row = read(lines[end]);
      if (!row || row.length !== cells.length) break;
      rows.push(row);
    }
    if (!rows.length) continue;
    const md = [cells, ...rows].map((row) => `| ${row.join(" | ")} |`);
    lines.splice(at, end - at, ...md);
    at += md.length - 1;
  }
  return lines.join("\n");
}

function rich(text, headings, program) {
  const out = [];
  let pairable = null; // 바로 앞에 놓은 예제 입력 {n, at}(같은 번호의 출력이 오면 두 칸으로 묶는다)
  String(text || "").split(/```[a-zA-Z0-9]*\n?/).forEach((part, i) => {
    if (i % 2) return out.push(`<pre class="code"><code>${esc(part.replace(/\s+$/, ""))}</code></pre>`);
    if (headings && !program) part = plainTables(part); // 문제 글(함수 방식)의 탭·공백 표
    let para = [], list = [], table = [], sample = null;
    const endSample = () => {
      if (!sample) return;
      const rows = sample.rows.join("\n").replace(/^\s*\n|\n\s*$/g, ""); // 앞뒤 빈 줄만 뗀다(줄 앞 공백은 답이다)
      const html = `<div class="sample"><h3>${esc(sample.head)}</h3>${rows.trim() ? `<pre class="code"><code>${esc(rows)}</code></pre>` : ""}</div>`;
      if (!sample.input && pairable && pairable.n === sample.n && pairable.at === out.length - 1) out[out.length - 1] = `<div class="io-pair">${out[out.length - 1]}${html}</div>`;
      else out.push(html);
      pairable = sample.input ? { n: sample.n, at: out.length - 1 } : null;
      sample = null;
    };
    const flush = (...keep) => {
      const what = (name) => keep.includes(name);
      if (para.length && !what("para")) { out.push(`<p>${para.map(inline).join("<br>")}</p>`); para = []; }
      if (list.length && !what("list")) { out.push(`<ul>${list.map((x) => `<li>${inline(x)}</li>`).join("")}</ul>`); list = []; }
      if (table.length && !what("table")) {
        const rows = table.map((row) => row.replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim())).filter((cells) => !cells.every((cell) => /^[-: ]*$/.test(cell)));
        out.push(`<div class="table-wrap"><table>${rows.map((cells, n) => `<tr>${cells.map((cell) => (n ? `<td>${inline(cell)}</td>` : `<th scope="col">${inline(cell)}</th>`)).join("")}</tr>`).join("")}</table></div>`);
        table = [];
      }
    };
    for (const line of part.split("\n")) {
      const t = line.trim(), head = program && SAMPLE_HEAD.exec(t);
      if (head) { flush(); endSample(); sample = { head: t.replace(/^#+\s*|\s*복사\s*:?$/g, ""), n: head[2], input: /입력|input/i.test(head[1]), rows: [], blank: 0 }; continue; }
      if (sample) {
        sample.blank = t ? 0 : sample.blank + 1;
        if (sample.blank < 2) { sample.rows.push(line); continue; }
        endSample();
        continue;
      }
      if (!t) { flush("table", "list"); continue; } // 빈 줄은 문단만 끊는다. 표와 목록은 다른 글이 올 때까지 잇는다
      if (t.startsWith("|") && t.length > 1) { flush("table"); table.push(t); continue; }
      if (/^[-•]\s+/.test(t)) { flush("list"); list.push(t.replace(/^[-•]\s+/, "")); continue; }
      const title = /^#{1,4}\s+(.+)$/.exec(t);
      if (title || (headings && HEADING.test(t))) { flush(); out.push(`<h3>${inline(title ? title[1] : t)}</h3>`); continue; }
      flush("para");
      para.push(t);
    }
    flush();
    endSample();
  });
  return out.join("");
}

const kindChip = (kind) => (kind ? `<span class="kind kind-${esc(kind)}">${KIND[kind] ? ico("k-" + kind) : ""}${esc((KIND[kind] || [kind])[0])}</span>` : ""); // 종류가 없으면(코드와 맞지 않아 서버가 비웠다) 꼬리표를 그리지 않는다
const meMsg = (text, sending) => `<div class="msg me${sending ? " sending" : ""}"><span class="who">나</span><div class="bubble">${esc(text)}</div></div>`;
const tutorBubble = (text) => `<div class="msg tutor"><span class="who">튜터</span><div class="bubble">${rich(text)}</div></div>`;

/* ── 화면 이동 ── */
function show(view) {
  const moved = S.view && S.view !== view;
  S.view = view;
  for (const name of ["list", "new", "code", "feedback", "report"]) $("view-" + name).hidden = name !== view;
  const editing = location.hash.startsWith("#/edit/"); // 문제 수정은 등록 화면을 쓰지만 문제 목록에 속한다
  for (const [id, on] of [["nav-list", editing || (view !== "new" && view !== "report")], ["nav-report", view === "report"], ["nav-new", view === "new" && !editing]]) on ? $(id).setAttribute("aria-current", "page") : $(id).removeAttribute("aria-current");
  $("main").scrollTop = 0;
  if (moved) { say(carried); carried = ""; } // 앞 화면의 상태 문구를 남기지 않는다
  if (view !== "code") document.title = "AlgoBlock";
  if (moved) $({ list: "list-title", new: "new-title-h", code: "p-title", feedback: "fb-title", report: "report-title" }[view]).focus();
}

function route() {
  flushSaves();
  // 화면을 옮기면(뒤로 가기 포함) 코드 칸·블록·문제의 확인 줄과 원본 보기 창을 닫는다(돌아왔을 때 남은 확인 줄을 눌러 코드를 잃지 않게)
  S.codeAsk = S.fillAsk = null;
  $("reset-confirm").hidden = $("del-confirm").hidden = true;
  $("reset").hidden = $("p-edit").hidden = $("p-delete").hidden = false;
  if ($("asset").open) closeAsset();
  const [a, b, c] = location.hash.replace(/^#\/?/, "").split("/");
  if (a === "p" && b) return c === "feedback" ? showFeedback(b) : showCode(b);
  if (a === "new") return showNew();
  if (a === "edit" && b) return showEdit(b);
  if (a === "report") return showReport();
  return showList();
}

function render() {
  if (S.view === "code") renderCode();
  if (S.view === "feedback") renderFeedback();
  applyBusy();
}

/* ── 02 문제 목록(홈): 입구 셋(문제 풀기 · 내 문제 넣기 · 내 기록) → 내 문제 → 기본 문제 단계(주제마다 한 줄, 단계마다 한 칸) ── */
const connected = () => !!(ACCOUNTS && ACCOUNTS.connected);
/** 다음 문제는 여기서 하나로 정한다: 학습 보고서의 ‘다음에 풀 문제’ 첫 문제(skipId는 뺀다). 홈의 ‘이어서 풀기’, 결과, 피드백, 보고서가 같이 쓴다. */
const nextOf = (next, skipId) => (next || []).find((n) => n.id !== skipId) || null;
const levelState = (p) => (p.solved ? ["done", "통과"] : p.submitted || p.touched ? ["tried", "푸는 중"] : ["", "아직 안 풂"]); // 제출이 없어도 코드를 손댔으면 푸는 중
/** 한 주제의 단계 칸들. 칸마다 그 단계의 문제로 간다(잠그지 않는다). 색은 단계, 채움·테두리·흐림은 상태. */
const levelCells = (name, mine) => `<span class="levels">${mine.map((p) => {
  const [cls, word] = levelState(p);
  return `<a class="lv l${p.level} ${cls}" href="#/p/${esc(p.id)}" title="${p.level}단계 · ${esc(p.title)} (${word})" aria-label="${esc(name)} ${p.level}단계 ${esc(p.title)}, ${word}">${p.level}</a>`;
}).join("")}</span>`;
const gdot = (key) => (GROUP[key] ? `<i class="gdot g-${GROUP[key]}" aria-hidden="true"></i>` : "");
const LEGEND = `<p class="hint legend"><span><i class="lv l1 done">1</i>통과(채움)</span><span><i class="lv l2 tried">2</i>푸는 중(테두리)</span><span><i class="lv l3">3</i>아직 안 풂(흐림)</span>
  <span>숫자가 단계예요. 1단계 청록에서 5단계 빨강으로 갈수록 어려워요.</span><span class="groups">${Object.entries(GROUP_NAME).map(([k, n]) => `<span><i class="gdot g-${k}" aria-hidden="true"></i>${n}</span>`).join("")}</span></p>`;

let LIST_LANG = ""; // 등록한 문제 목록에서 고른 언어(빈 글은 전체)
async function showList() {
  show("list");
  const [r, rep] = await Promise.all([api("/api/problems"), api("/api/report")]);
  if (S.view !== "list") return;
  if (!r.ok) return void ($("list-body").innerHTML = noteHtml(errorNote(r.error)));
  const all = r.data.problems, built = all.filter((p) => p.builtin);
  const sum = rep.ok ? rep.data.summary : null, next = rep.ok ? nextOf(rep.data.next) : null, fresh = !!sum && !sum.submissions, ai = connected();
  // 위: 입구 셋. 카드마다 누르면 생기는 일 한 줄, 주 동작은 '문제 풀기'의 단추 하나
  $("entries").innerHTML = !sum ? "" : `<section class="entry main" aria-labelledby="entry-solve">
      <h2 class="entry-label" id="entry-solve">문제 풀기</h2>
      ${next ? `<p class="entry-title">${esc(next.title)}</p><p class="entry-why">${lvBadge(next.level)}${next.theme_name ? `<span>${esc(next.theme_name)}</span>` : ""}<span>${esc(next.why)}</span></p>`
    : '<p class="entry-title">기본 문제를 모두 풀었어요</p><p class="entry-why">아래에서 다시 풀 문제를 골라요.</p>'}
      <p class="entry-tutor">${ai ? `<span class="dot" aria-hidden="true"></span>막히면 튜터가 질문으로 이끌어요 · ${esc(CONN.name)} 연결됨`
    : '막히면 튜터가 질문으로 이끌어요. 튜터는 AI를 연결하면 써요 — <button type="button" class="link-btn" id="note-conn">연결하기</button>'}</p>
      ${next ? `<div class="entry-do"><a class="btn primary big" href="#/p/${esc(next.id)}">${fresh ? "첫 문제 풀기" : "이어서 풀기"}</a><span class="hint">누르면 문제와 코드 칸이 열려요.</span></div>` : ""}
    </section>
    <section class="entry" aria-labelledby="entry-new"><h2 class="entry-label" id="entry-new">내 문제 넣기</h2>
      <p>가진 문제를 글이나 사진으로 넣어 같은 방식으로 풀어요.</p>
      <div class="entry-do"><a class="btn" href="#/new">${ico("i-plus")}내 문제 넣기</a><span class="hint">글 넣기 → 확인하기 → 등록, 세 걸음이에요.</span></div></section>
    <section class="entry" aria-labelledby="entry-me"><h2 class="entry-label" id="entry-me">내 기록</h2>
      <p><strong class="num">${sum.solved}</strong> / ${sum.total} 문제 통과 · 출석 ${rep.data.attendance.days}일</p>
      <div class="entry-do"><a class="btn" href="#/report">${ico("i-chart")}학습 보고서 보기</a><span class="hint">강한 주제와 더 공부할 주제를 찾아요.</span></div></section>`;
  // 등록한 문제가 6개 이상이면 머리 옆에 언어 칩(전체 + 목록에 있는 언어). 화면에서만 거르고, 새로 고치면 전체로
  const ownLangs = [...new Set(all.filter((p) => !p.sample).map((p) => p.language))];
  if (!ownLangs.includes(LIST_LANG)) LIST_LANG = "";
  const chips = (list) => (list.length < 6 ? "" : `<div class="picks lang-filter" role="group" aria-label="등록한 문제를 언어로 거르기">${["", ...ownLangs].map((k) =>
    `<button type="button" class="pick" data-lang-filter="${esc(k)}" aria-pressed="${k === LIST_LANG}">${k ? esc(LANG[k] || k) : "전체"}</button>`).join("")}</div>`);
  const group = (id, title, list, filter) => (!list.length ? "" : `<div class="list-head"><h2 class="list-label" id="${id}">${title} ${list.length}개</h2>${filter ? chips(list) : ""}</div>
    <ul class="rows" aria-labelledby="${id}">${list.map((p) => `<li${filter ? ` data-lang="${esc(p.language)}"${LIST_LANG && p.language !== LIST_LANG && list.length >= 6 ? " hidden" : ""}` : ""}><a class="row" href="#/p/${esc(p.id)}">
      <span><span class="row-title">${esc(p.title)}</span>
        <span class="badges">${lvBadge(p.level, p.level_by === "analysis")}${themeChip(p.theme, p.theme_name)}${verifiedBadge(p)}${tagChips(p.tags)}</span>
        <span class="row-meta">${esc(LANG[p.language] || p.language)} · ${p.submitted ? `통과 ${p.passed} · 제출 ${p.submitted}` : "아직 풀지 않았어요"}</span></span>
      <span></span>${ico("i-caret")}<span class="sr-only">열기</span></a></li>`).join("")}</ul>`);
  let html = group("list-own", "내 문제", all.filter((p) => !p.sample), true);
  if (built.length) {
    html += `<div class="list-head"><h2 class="list-label" id="list-builtin">기본 문제 · 주제 ${r.data.themes.length}개</h2><span class="hint">주제마다 1단계부터 5단계까지 차례로 풀어요. 칸을 누르면 그 단계 문제가 열려요.</span></div>${LEGEND}
      <ul class="ladders" aria-labelledby="list-builtin">${r.data.themes.map((t) => `<li class="ladder-row">
        <span class="ladder-name">${gdot(t.key)}${esc(t.name)}<small>${t.solved}/${t.total}</small></span>
        ${levelCells(t.name, built.filter((p) => p.theme === t.key))}
        ${!t.next ? `<span class="ladder-next all">${ico("i-check")}모두 풀었어요</span>` : next && t.next.id === next.id ? '<span class="ladder-next here">위 ‘문제 풀기’의 문제예요</span>'
    : `<a class="ladder-next" href="#/p/${esc(t.next.id)}"><span class="muted">다음</span><span class="ladder-next-title">${esc(t.next.title)}</span>${ico("i-caret")}</a>`}
      </li>`).join("")}</ul>`;
  }
  html += group("list-sample", "예시 문제", all.filter((p) => p.sample && !p.builtin)); // 개발할 때만 보인다
  $("list-body").innerHTML = html || '<div class="card"><div class="prose"><p>아직 문제가 없어요. ‘내 문제 넣기’로 가진 문제를 넣어 보세요.</p></div></div>';
}

/* ── 학습 보고서: 서버가 기록에서 계산해 준 것을 그린다(모델 0회) ── */
const STATE_WORD = { strong: "강점", weak: "더 공부", progress: "진행 중", new: "새로" };
const FAIL_WORD = { failed: "오답", runtime_error: "실행 오류", timeout: "시간 초과", compile_error: "컴파일·형식 오류" }; // 언어를 잘못 골라 함수를 못 찾은 제출도 컴파일·형식 오류로 센다
/** 통과하지 못한 제출의 가장 많은 종류와 할 일. 수가 같으면 하나를 고르지 않고 나란히 말한다. */
const FAIL_TIP = { timeout: "제한사항의 입력 크기를 먼저 보고 방법을 고르세요.", failed: "제출 전에 ‘예시 실행’과 경계 입력(가장 작은 값, 같은 값)을 손으로 따져 보세요.",
  other: "빈 입력과 범위를 벗어나는 위치를 확인하세요." };
function failTip(fails) {
  const max = Math.max(...fails.map(([, n]) => n)), top = fails.filter(([, n]) => n === max).map(([kind]) => kind);
  const tips = [...new Set(top.map((kind) => FAIL_TIP[kind] || FAIL_TIP.other))].join(" ");
  if (top.length > 1) return `가장 많은 것: ${top.map((kind) => FAIL_WORD[kind]).join(" · ")}(같은 수). ${tips}`;
  return `${top[0] === "timeout" ? "시간 초과가 가장 많아요." : top[0] === "failed" ? "오답이 가장 많아요." : "코드가 돌다가 멈추는 일이 많아요."} ${tips}`;
}
const when = (at) => String(at || "").slice(0, 16).replace("T", " ");

async function showReport() {
  show("report");
  const [rep, ps] = await Promise.all([api("/api/report"), api("/api/problems")]);
  if (S.view !== "report") return;
  if (!rep.ok) return void ($("report-body").innerHTML = noteHtml(errorNote(rep.error)));
  const d = rep.data, sum = d.summary, built = ps.ok ? ps.data.problems.filter((p) => p.builtin) : [];
  const touched = d.themes.some((t) => t.state !== "new"), fresh = !sum.submissions && !touched;
  const att = d.attendance, came = att.recent.filter(Boolean).length; // 출석 칸의 색은 단계 색이 아니다(출석·결석만)
  // 맨 위: 한 줄 요약과 주 동작 하나(기록이 없으면 첫 문제, 있으면 약한 주제의 다음 문제)
  const weak = d.weaknesses.find((x) => x.next), target = !fresh && weak ? { ...weak.next, why: weak.name } : nextOf(d.next);
  const label = fresh ? "첫 문제 풀기" : weak ? "더 공부할 문제 풀기" : "다음 문제 풀기";
  let html = `<section class="report-top"><div><p class="report-line">${fresh ? "아직 기록이 없어요. 문제를 풀고 제출하면 주제별 진행과 약한 주제가 여기에 쌓여요."
    : `통과 <strong>${sum.solved}</strong> / ${sum.total} · 제출 ${sum.submissions}번 · 첫 제출에 통과 ${Math.round(100 * sum.first_try_rate)}% · 출석 ${att.days}일`}</p>
    ${target ? `<p class="hint">${fresh ? "" : weak ? `더 공부할 주제: ${esc(weak.name)} · ` : ""}${esc(target.title)}</p>` : ""}</div>
    ${target ? `<a class="btn primary big" href="#/p/${esc(target.id)}">${label}</a>` : ""}</section>`;
  if (fresh) return void ($("report-body").innerHTML = html);
  const fails = Object.keys(FAIL_WORD).map((kind) => [kind, sum.fails[kind] || 0]); // 기본 문제와 등록한 문제의 제출을 모두 센다
  const failMax = Math.max(1, ...fails.map(([, n]) => n)), failAll = fails.reduce((n, [, c]) => n + c, 0);
  const langs = Object.entries(sum.languages).sort((x, y) => y[1] - x[1]).map(([k, n]) => `${LANG[k] || k} ${n}`).join(" · ");
  html += `<section class="tiles" aria-label="요약">
    <div class="tile"><span class="tile-label">통과한 기본 문제</span><strong>${sum.solved}<small> / ${sum.total}</small></strong><span class="bar" aria-hidden="true"><i style="width:${sum.total ? Math.round(100 * sum.solved / sum.total) : 0}%"></i></span>${sum.own.total ? `<span class="tile-sub">등록한 문제 ${sum.own.solved} / ${sum.own.total}</span>` : ""}</div>
    <div class="tile"><span class="tile-label">제출</span><strong>${sum.submissions}<small>번</small></strong><span class="tile-sub">${esc(langs || "아직 없어요")}</span></div>
    <div class="tile"><span class="tile-label">첫 제출에 통과</span><strong>${Math.round(100 * sum.first_try_rate)}<small>%</small></strong><span class="tile-sub">제출한 문제 가운데 첫 제출에 통과한 비율</span></div>
    <div class="tile"><span class="tile-label">출석</span><strong>${att.days}<small>일</small></strong>
      <span class="days" role="img" aria-label="최근 14일 가운데 ${came}일 출석">${att.recent.map((on) => `<i${on ? ' class="on"' : ""}></i>`).join("")}</span></div>
  </section>`;
  // 준비도(도움 없이 푼 기본 문제로만)와 다음 단계까지 남은 주제(학습 지도 순서), 여러 주제에서 되풀이된 실패. 빈 카드는 보이지 않는다
  const rd = d.readiness, focus = rd.focus, SHOWN = 5; // 남은 주제는 앞의 다섯 줄만 펼쳐 두고 나머지는 접는다
  const lefts = (rows) => `<ul class="points plain">${rows.map((x) => `<li><strong>${esc(x.name)}</strong>
      <span>${esc(x.todo)}${x.after.length ? ` · 먼저 ${esc(x.after.join(", "))}` : ""}</span></li>`).join("")}</ul>`;
  html += `<div class="sides${d.patterns.length ? "" : " full"}"><section class="card side"><h2>준비도 <span class="muted">${esc(rd.label)}</span></h2><p>${esc(rd.line)}</p>
    ${focus ? `<p class="hint">다음에 배울 주제: <strong>${esc(focus.name)}</strong>${focus.next ? ` · <a class="link" href="#/p/${esc(focus.next.id)}">${esc(focus.next.title)}</a>` : ""}</p>` : ""}
    ${rd.remaining.length ? `<p class="hint">${esc(rd.goal)}까지 남은 주제</p>${lefts(rd.remaining.slice(0, SHOWN))}` : ""}
    ${rd.remaining.length > SHOWN ? `<details class="signal-group"><summary>나머지 ${rd.remaining.length - SHOWN}개 주제 보기</summary>${lefts(rd.remaining.slice(SHOWN))}</details>` : ""}
    <details class="signal-group"><summary>기준 보기</summary><ul class="plain-list">${rd.rules.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></details>
    <p class="hint">${esc(rd.basis)}</p></section>
    ${d.patterns.length ? `<section class="card side"><h2>여러 주제에서 되풀이된 실패</h2><ul class="points">${d.patterns.map((x) => `<li>${esc(x.line)}</li>`).join("")}</ul></section>` : ""}</div>`;
  const side = (title, rows, cls) => `<section class="card side ${cls}"><h2>${title}</h2><ul class="points">${rows.map((x) => `<li><strong>${esc(x.name)}</strong><span>${esc(x.why)}</span>
    ${x.next && !(target && x.next.id === target.id) ? `<a class="link" href="#/p/${esc(x.next.id)}">다음에 풀 문제: ${esc(x.next.title)}</a>` : ""}</li>`).join("")}</ul></section>`;
  const sides = [d.weaknesses.length ? side("더 공부할 주제", d.weaknesses, "weak") : "", d.strengths.length ? side("강한 주제", d.strengths, "strong") : ""].filter(Boolean); // 빈 카드는 보이지 않는다
  if (sides.length) html += `<div class="sides">${sides.join("")}</div>`;
  const nexts = d.next; // 첫 줄이 홈의 ‘이어서 풀기’와 결과·피드백의 ‘다음 문제’다
  if (nexts.length) html += `<h2 class="list-label">다음에 풀 문제</h2><ul class="rows">${nexts.map((n) => `<li><a class="row" href="#/p/${esc(n.id)}"><span><span class="row-title">${esc(n.title)}</span>
    <span class="badges">${lvBadge(n.level)}${n.theme_name ? `<span class="theme-chip">${esc(n.theme_name)}</span>` : ""}</span><span class="row-meta">${esc(n.why)}</span></span><span></span>${ico("i-caret")}<span class="sr-only">열기</span></a></li>`).join("")}</ul>`;
  const fold = (title, count, body) => `<details class="fold card"><summary><span>${title}</span> <span class="muted">${count}</span></summary>${body}</details>`;
  html += fold("주제별 진행", `${d.themes.length}개 주제 · 통과 ${sum.solved}`, `${LEGEND}<ul class="ladders report">${d.themes.map((t) => `<li class="ladder-row">
    <span class="ladder-name">${gdot(t.key)}${esc(t.name)}<small>${t.solved}/${t.total}</small></span>
    ${levelCells(t.name, built.filter((p) => p.theme === t.key))}
    <span class="state ${t.state}">${STATE_WORD[t.state]}</span>
    <span class="ladder-why">${esc(t.why)}${t.submissions ? ` <span class="muted">제출 ${t.submissions}번${t.hints ? ` · 힌트 ${t.hints}개` : ""}${t.solution_before_pass ? ` · 해설 먼저 ${t.solution_before_pass}문제` : ""}</span>` : ""}${(t.plan_differs || []).map((x) => // 고른 주제와 풀이 계획의 유형을 나란히
      ` <span class="muted">· ‘${esc(x.title)}’: 고른 주제 ${esc(t.name)}, 풀이 계획 ${esc(x.planned)}</span>`).join("")}</span>
  </li>`).join("")}</ul>`);
  const cards = [failAll ? `<section class="card side"><h2>통과하지 못한 제출</h2><ul class="bars">${fails.map(([kind, n]) => `<li><span>${FAIL_WORD[kind]}</span><span class="bar" aria-hidden="true"><i class="${kind}" style="width:${Math.round(100 * n / failMax)}%"></i></span><b>${n}</b></li>`).join("")}</ul>
      <p class="hint">${failTip(fails)}</p></section>` : "",
    d.pitfalls.length ? `<section class="card side"><h2>되풀이한 실수</h2><ul class="points plain">${d.pitfalls.map((x) => `<li><strong>${esc(x.name)}</strong><span>${x.count}번</span></li>`).join("")}</ul></section>` : ""].filter(Boolean);
  if (cards.length) html += `<div class="sides">${cards.join("")}</div>`;
  if (d.signals.length) html += fold("실전 신호 모음", `${d.signals.reduce((n, g) => n + g.items.length, 0)}개`, `<p class="hint">통과한 문제에서 모았어요. 실전에서 이런 표현을 보면 이 방법을 떠올려요.</p>
    ${d.signals.map((g) => `<details class="signal-group"><summary>${esc(g.name)} <span class="muted">${g.items.length}개</span></summary><ul class="signals">${g.items.map((x) => `<li class="signal"><q>${esc(x.phrase)}</q><span>${esc(x.means)}</span><small>${esc(x.title)}</small></li>`).join("")}</ul></details>`).join("")}`);
  if (d.feedbacks.length) html += `<h2 class="list-label">받은 AI 피드백</h2><ul class="rows">${d.feedbacks.map((f) => `<li><a class="row" href="#/p/${esc(f.id)}/feedback"><span><span class="row-title">${esc(f.title)}</span>
    <span class="row-meta">${esc(when(f.at))}${f.summary ? ` · ${esc(f.summary.length > 90 ? `${f.summary.slice(0, 90).replace(/\s*\S*$/, "")}…` : f.summary)}` : ""}</span></span><span></span>${ico("i-caret")}<span class="sr-only">피드백 열기</span></a></li>`).join("")}</ul>`;
  if (d.recent.length) html += fold("최근 제출", `${d.recent.length}개`, `<ul class="rows recent">${d.recent.map((x) => `<li><a class="row" href="#/p/${esc(x.id)}"><span><span class="row-title">${esc(x.title)}</span>
    <span class="row-meta">${esc(LANG[x.language] || x.language)} · ${esc(when(x.at))}</span></span><span class="state ${x.ok ? "strong" : "weak"}">${x.ok ? "통과" : esc(FAIL_WORD[x.status] || CASE_STATE[x.status] || "통과 못 함")}</span>${ico("i-caret")}</a></li>`).join("")}</ul>`);
  $("report-body").innerHTML = html;
}

/* ── 03 문제 등록 ── */
function addCaseRow() {
  const n = $("case-rows").children.length + 1, stdin = $("new-mode").value === "program";
  const row = document.createElement("div");
  row.className = `case-row${stdin ? " program" : ""}`;
  const text = (id, label, hint) => `<textarea id="${id}" class="case-val" rows="2" aria-label="${label}" placeholder="${hint}" spellcheck="false" autocapitalize="off" wrap="off"></textarea>`;
  row.innerHTML = `<span class="no">${n}</span>
    ${stdin ? text(`case-input-${n}`, `${n}번 케이스 입력`, "입력  예: 3 5") + text(`case-expected-${n}`, `${n}번 케이스 기대 출력`, "기대 출력  예: 8")
    : `<input type="text" id="case-input-${n}" class="case-val" aria-label="${n}번 케이스 넣을 값" aria-describedby="case-call-${n}" placeholder="넣을 값  예: [[1, 2, 3], 5]" autocomplete="off" spellcheck="false">
    <input type="text" id="case-expected-${n}" class="case-val" aria-label="${n}번 케이스 기대 결과" placeholder="기대 결과  예: 2" autocomplete="off" spellcheck="false">`}
    <label class="case-hide" title="켜면 숨은 테스트: 제출할 때만 돌리고 통과 여부만 보여요"><input type="checkbox" id="case-hidden-${n}" aria-label="${n}번 케이스 숨김">숨김</label>
    <button type="button" class="btn quiet small" data-case-clear="${n}" aria-label="${n}번 케이스 비우기">비우기</button>
    ${stdin ? "" : `<small class="case-call" id="case-call-${n}"></small>`}<small class="case-diff" hidden>글의 표와 달라요</small>`;
  $("case-rows").append(row);
}

/** 케이스 줄의 [넣을 값(입력), 기대 결과(기대 출력), 숨김]. 함수 방식은 한 줄 칸, 표준 입출력은 여러 줄 칸이다. */
const caseCells = (row) => [...row.querySelectorAll(".case-val"), row.querySelector("input[type=checkbox]")];

/** 푸는 방식에 맞춘 케이스 안내. 방식을 바꾸면 적던 값은 그대로 새 꼴의 줄로 옮긴다. */
function caseHelp() {
  const stdin = $("new-mode").value === "program";
  $("case-help").textContent = stdin ? "입력은 프로그램의 표준 입력에 그대로 넣어요." : "넣을 값은 solution에 넘길 값을 순서대로 대괄호 안에 적어요.";
  $("case-fill-ask").textContent = stdin ? "지금 적힌 케이스를 예제의 것으로 바꿀까요?" : "지금 적힌 케이스를 표의 것으로 바꿀까요?";
}

function setCaseMode() {
  const rows = formCases();
  $("case-rows").innerHTML = "";
  for (const x of rows) {
    addCaseRow();
    const [a, b, h] = caseCells($("case-rows").lastElementChild);
    a.value = x.input;
    b.value = x.expected;
    h.checked = x.hidden;
    showCall(a);
  }
  $("case-fill-confirm").hidden = $("case-note").hidden = true;
  caseHelp();
  syncForm();
  markTableDiff();
  findTable();
}

/** 케이스 줄의 '넣을 값'이 풀이 함수에 어떻게 넘어가는지 그 아래에 보여 준다(JSON 목록으로 읽힐 때만). */
function showCall(input) {
  const row = input.closest(".case-row"), out = row.querySelector(".case-call");
  if (!out) return void row.querySelectorAll("textarea").forEach(grow); // 표준 입출력은 입력을 그대로 넣는다. 칸 높이만 글에 맞춘다
  let args = null;
  try { args = JSON.parse(input.value); } catch (e) { /* 아직 읽히지 않는다 */ }
  out.textContent = Array.isArray(args) ? `→ ${callText(input.value)}` : "";
}

/* 입출력 예 표에서 케이스 채우기: 표 찾기는 서버가 규칙으로 한다(모델 0회). 글이 바뀌면 잠깐 멈췄을 때 다시 찾아 단추를 보이거나 숨긴다.
   NAMES: 표 머리의 인자 이름(채웠을 때만 등록·수정에 같이 보내 시작 코드의 인자 이름이 된다) */
let tableTimer = null, NAMES = null, TABLE = null, readOcr = false; // TABLE: 표에서 채운 케이스(고친 값을 견준다), readOcr: 글자 읽기로 읽은 글
const sameVal = (a, b) => { try { return JSON.stringify(JSON.parse(a)) === JSON.stringify(JSON.parse(b)); } catch (e) { return a.trim() === b.trim(); } };
/** 표에서 채운 케이스를 표와 다르게 고친 줄에 '글의 표와 달라요'(막지는 않는다). */
function markTableDiff() {
  [...$("case-rows").children].forEach((row, i) => {
    const t = TABLE && TABLE[i], [a, b] = caseCells(row), note = row.querySelector(".case-diff");
    if (note) note.hidden = !t || !(a.value.trim() || b.value.trim()) || (sameVal(a.value, t.input) && sameVal(b.value, t.expected));
  });
}
const findTableSoon = () => { clearTimeout(tableTimer); tableTimer = setTimeout(findTable, 400); };
async function findTable() {
  const text = $("new-text").value, mode = $("new-mode").value, r = await api("/api/problems/cases", { text, mode });
  if (S.view !== "new" || text !== $("new-text").value || mode !== $("new-mode").value) return;
  $("case-fill").hidden = !(r.ok && (r.data.cases.length || r.data.skipped));
  // 다른 방식(함수 ↔ 표준 입출력)으로 찾은 케이스가 있으면 방식을 바꾸자고 한다. 수정에서는 방식을 바꾸지 않는다
  const program = mode === "program", other = r.ok && r.data.other > 0 && !EDIT;
  $("mode-guess").hidden = !other;
  $("mode-guess-text").textContent = program ? "함수(solution) 문제처럼 보여요." : "표준 입출력 문제처럼 보여요.";
  $("mode-switch").textContent = program ? "함수로 바꾸기" : "표준 입출력으로 바꾸기";
}

/** 등록 화면의 작은 안내: 실수 허용 오차(함수 방식에서 케이스에 실수가 있을 때), '새로 쓰기'(적은 것이 있을 때. 수정 화면은 아니다). */
const hasFloat = (t) => /\d\.\d|\d[eE][-+]?\d/.test(String(t).replace(/"(?:\\.|[^"\\])*"/g, "")); // 문자열 안은 보지 않는다
function syncForm() {
  const rows = formCases();
  $("case-float").hidden = $("new-mode").value === "program" || !rows.some((x) => hasFloat(x.input) || hasFloat(x.expected));
  $("case-names-field").hidden = $("new-mode").value === "program" || !!NAMES; // 표 머리에서 이름을 얻지 못한 함수 문제만: 글의 이름을 직접 적을 수 있다
  $("case-flags").hidden = $("new-mode").value !== "program"; // 답 비교 표시(실수 답·답이 여럿)는 표준 입출력 문제에만
  const draft = !!($("new-title").value.trim() || $("new-text").value.trim() || $("new-theme").value || FILES.length || rows.some((x) => x.input.trim() || x.expected.trim()));
  $("new-clear").hidden = !!EDIT || !draft || !$("new-clear-confirm").hidden;
  if (!draft) $("new-clear-confirm").hidden = true;
}

async function fillCases(sure, quiet) {
  $("case-fill-confirm").hidden = true;
  const stdin = $("new-mode").value === "program", r = await api("/api/problems/cases", { text: $("new-text").value, mode: $("new-mode").value });
  if (!r.ok) return newError(errorNote(r.error).text);
  const { cases, skipped, names } = r.data;
  const missed = (!skipped ? "" : stdin ? `예제 ${skipped}개는 출력을 찾지 못해 넣지 않았어요. 직접 넣어 주세요. ` : `표의 ${skipped}줄은 읽지 못했어요. 직접 넣어 주세요. `)
    + (r.data.spill || []).join(" "); // 기대 출력에 빈 줄 뒤로 글이 더 있다(힌트·출처 글이 섞였을 수 있다)
  if (cases.length && !sure && formCases().some((x) => x.input.trim() || x.expected.trim())) { // 이미 적힌 케이스가 있으면 먼저 묻는다
    $("case-note").hidden = true; // 묻는 동안에는 '채웠어요'를 보이지 않는다(답한 뒤에)
    $("case-fill-confirm").hidden = false;
    return $("case-fill-no").focus();
  }
  // 글자 읽기로 읽은 글은 줄이 깨져 빠질 수 있다. 채운 수를 원본과 견주게 한다
  $("case-note").textContent = (cases.length ? `글의 입출력 예에서 케이스 ${cases.length}개를 채웠어요. ${readOcr ? "원본의 예시 수와 견줘 주세요. " : ""}` : "") + missed
    || (r.data.other > 0 && !EDIT ? `${stdin ? "함수(solution)" : "표준 입출력"} 꼴의 예시 ${r.data.other}개를 찾았어요. 푸는 방식을 바꾸면 채워요.` // 다른 방식으로는 찾았다: 위 알림과 어긋나지 않게 한 가지로 말한다
      : "글에서 입출력 예를 찾지 못했어요. 아래에 직접 넣어 주세요."); // 문장으로만 적힌 예시는 읽지 못한다: 조용히 넘어가지 않고 알린다
  $("case-note").hidden = false;
  if (!cases.length) return void ($("case-fill").hidden = !skipped);
  TABLE = cases;
  $("case-rows").innerHTML = "";
  for (const x of cases) {
    addCaseRow();
    const [a, b] = caseCells($("case-rows").lastElementChild);
    a.value = x.input;
    b.value = x.expected;
    showCall(a);
  }
  NAMES = names;
  syncForm();
  markTableDiff();
  say(`입출력 예에서 케이스 ${cases.length}개를 채웠어요.`);
  if (!quiet) $("case-input-1").focus();
}

/** 등록 화면의 케이스 칸을 처음으로(케이스 한 줄, 표 단추·확인·알림 숨김). */
function resetCases() {
  $("case-rows").innerHTML = "";
  addCaseRow();
  NAMES = TABLE = null;
  $("case-fill").hidden = $("case-fill-confirm").hidden = $("case-note").hidden = $("mode-guess").hidden = true;
  caseHelp();
  syncForm();
}

/** 등록 화면을 비운다(등록·수정 뒤, 수정에서 등록으로 올 때, '새로 쓰기'). */
function emptyForm() {
  $("new-form").reset();
  showDoubts([]);
  readOcr = false;
  autoTitle = "";
  $("new-lang")._filled = false;
  resetCases();
  setFiles([]);
}

/* 같은 화면을 문항 수정에도 쓴다(#/edit/<id>). EDIT: 고치는 문항 {id, text, cases}(바뀌었는지 볼 원래 값) */
let EDIT = null;
const formCases = () => [...$("case-rows").children].map((row) => { const [a, b, h] = caseCells(row); return { input: a.value, expected: b.value, hidden: h.checked }; });
/** 답 비교 표시(표준 입출력 문제만 보낸다. 사용자가 켤 때만 켜진다). flagKey: 수정에서 바뀌었는지 견줄 값 */
const answerFlags = () => ($("new-mode").value === "program" ? { float_output: $("new-float").checked, many_answers: $("new-many").checked } : {});
const flagKey = () => `${$("new-float").checked} ${$("new-many").checked}`;
const caseKey = (rows) => JSON.stringify(rows.map((x) => [String(x.input).trim(), String(x.expected).trim(), !!x.hidden]).filter(([a, b]) => a || b));
const langOptions = (list) => list.map((x) => `<option value="${esc(x)}">${esc(LANG[x] || x)}${TOOLS && TOOLS[x] === false ? " · 도구 없음" : ""}</option>`).join("");

/* 올린 파일: 올린 순서대로 1부터. 항목은 {name, kind, image, url, file}(새로 올린 것) 또는 {…, asset}(수정 화면에서 보관된 원본).
   수정 화면에서는 목록을 건드렸을 때만(filesTouched) 원본을 통째로 바꾼다 */
const FILE_KINDS = ["png", "jpg", "jpeg", "webp", "gif", "pdf", "md", "txt"];
const IMAGE_KINDS = ["png", "jpg", "jpeg", "webp", "gif"];
const TEXT_KINDS = ["md", "txt", "pdf"];
let FILES = [];
let filesTouched = false;
let filesRead = false; // 지금 파일 목록에서 글을 읽어 왔다
let readBase = null; // 처음 읽어 오기 전에 사용자가 적은 글(다시 읽을 때는 이것만 보낸다. 읽어 온 글이 두 벌이 되지 않게)
const kindOf = (name) => (/\.([^.]+)$/.exec(name) || ["", ""])[1].toLowerCase();

function newError(text, conn, field) {
  const box = $("new-error"), el = field && $(field);
  box.innerHTML = `<span>${esc(text)}</span>${conn ? '<button type="button" class="btn small" id="note-conn">연결하기</button>' : ""}`;
  if (el) { (el.closest(".field, fieldset") || el).after(box); el.setAttribute("aria-invalid", "true"); el.focus(); } // 그 칸 바로 아래
  else $("new-form").querySelector(".wizard-nav").before(box);
  box.hidden = false;
}
/** 오류를 걷는다(칸을 고치면). */
function clearError() {
  $("new-error").hidden = true;
  document.querySelectorAll("#new-form [aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
}

/* 세 걸음: 1 글 넣기 → 2 확인하기 → 3 등록. 칸마다 data-in으로 보일 걸음을 적어 두고 CSS가 가린다 */
let WSTEP = 1;
const WSTEP_TITLE = { 1: "문제 글을 넣어요", 2: "읽은 글과 예시를 확인해요", 3: "등록해요" };
function setStep(n, focus = true) {
  WSTEP = n;
  $("new-form").dataset.step = n;
  document.querySelectorAll("#wsteps li").forEach((li) => { const k = Number(li.dataset.wstep); li.className = k === n ? "now" : k < n ? "done" : ""; k === n ? li.setAttribute("aria-current", "step") : li.removeAttribute("aria-current"); });
  $("wstep-title").textContent = `${n}. ${n === 3 && EDIT ? "저장해요" : WSTEP_TITLE[n]}`;
  $("new-back").hidden = n === 1 || (!!EDIT && n === 2);
  $("new-next").hidden = n === 3;
  $("new-submit").hidden = n !== 3;
  $("edit-confirm").hidden = true;
  clearError();
  if (n === 3) renderSummary();
  if (focus) $("wstep-title").focus();
}

/** 걸음마다의 '다음': 1에서는 파일을 읽고(필요하면) 제목과 케이스를 채운다. 2에서는 빠진 것을 그 칸 아래에 알린다. */
async function nextStep() {
  if (WSTEP === 1) {
    if (FILES.length && !filesRead && !(await readFiles())) return; // 사진·PDF는 여기서 읽는다
    if (!$("new-text").value.trim()) return newError("문제 글을 붙여 넣거나 파일을 넣어 주세요.", false, "new-text");
    if (!$("new-title").value.trim()) $("new-title").value = autoTitle = titleOf($("new-text").value);
    if (!formCases().some((x) => x.input.trim() || x.expected.trim())) await fillCases(true, true); // 비어 있을 때만 입출력 예에서 채운다
    return setStep(2);
  }
  if (!$("new-title").value.trim()) return newError("제목을 적어 주세요.", false, "new-title");
  if (!formCases().some((x) => x.input.trim() && x.expected.trim())) return newError("테스트 케이스를 하나 이상 적어 주세요." + ($("case-fill").hidden ? "" : " 글에 입출력 예 표가 있으면 ‘입출력 예에서 채우기’를 눌러요."), false, "case-input-1");
  setStep(3);
}

/** 수정에서 글(공백 차이는 빼고)이나 케이스를 바꿨다: 서버가 풀이를 다시 준비할 수 있다(edit). */
const editRedo = () => !!EDIT && (EDIT.text.split(/\s+/).join(" ") !== $("new-text").value.trim().split(/\s+/).join(" ") || EDIT.cases !== caseKey(formCases()) || EDIT.flags !== flagKey());
/** 3 등록: 요약과 등록하면 생기는 일. */
function renderSummary() {
  const rows = formCases().filter((x) => x.input.trim() || x.expected.trim()), hidden = rows.filter((x) => x.hidden).length, ai = connected();
  const lang = $("new-lang").selectedOptions[0], mode = $("new-mode").selectedOptions[0];
  const flags = answerFlags(), many = !!flags.many_answers, marks = [flags.float_output && "실수 답", many && "답이 여럿일 수 있음"].filter(Boolean);
  $("new-summary").innerHTML = `<dl class="sum-list"><dt>제목</dt><dd>${esc($("new-title").value)}</dd>
    <dt>예시</dt><dd>${rows.length - hidden}개${hidden ? ` · 숨은 케이스 ${hidden}개` : ""}</dd>
    <dt>푸는 방식</dt><dd>${esc(EDIT ? mode.textContent : `${lang ? lang.textContent : ""} · ${mode.textContent}`)}</dd>
    <dt>주제 · 단계</dt><dd>${esc($("new-theme").value ? $("new-theme").selectedOptions[0].textContent : "자동")} · ${esc($("new-level").value ? `${$("new-level").value}단계` : "자동")}</dd>
    ${marks.length ? `<dt>답 비교</dt><dd>${esc(marks.join(" · "))}</dd>` : ""}</dl>
    ${EDIT ? `<p class="note">${editRedo() && ai ? "글이나 케이스, 답 비교가 바뀌어 튜터가 풀이를 다시 준비할 수 있어요. 모델을 쓰고 1분 안팎 걸려요." : "저장하면 바로 바뀌어요."}</p>` : `<p class="note${ai ? "" : " warn"}">${ai ? `등록하면 튜터가 풀이${many ? "를" : "와 숨은 테스트를"} 준비해요. 모델을 쓰고 1분 안팎 걸려요. 그동안 문제를 읽고 풀기 시작해도 돼요.`
    : `AI가 연결되지 않아 적은 예시만으로 채점해요.${many ? "" : " 연결하면 튜터가 숨은 테스트를 만들어 줘요."}`}${many ? " 답이 여럿일 수 있는 문제라 숨은 테스트는 만들지 않아요." : ""}</p>`}`;
}

function renderFiles() {
  $("file-list").hidden = !FILES.length;
  $("read-files").hidden = !FILES.length || filesRead; // 읽어 온 뒤에는 파일 목록이 바뀌기 전까지 숨긴다(같은 글이 또 붙지 않게)
  $("read-done").hidden = !FILES.length || !filesRead || !!S.busy;
  syncForm();
  $("file-list").innerHTML = FILES.map((x, i) => `<li class="file"><span class="no">${i + 1}</span>${x.image ? `<img src="${esc(x.url)}" alt="${esc(x.name)}" title="${esc(x.name)}">` : `<span class="file-name">${esc(x.name)}</span>`}
    <button type="button" class="btn quiet small" data-file-drop="${i}" aria-label="${i + 1}번 파일 빼기">빼기</button></li>`).join("");
}

function setFiles(list) {
  FILES.forEach((x) => { if (x.file) URL.revokeObjectURL(x.url); });
  FILES = list;
  filesTouched = false;
  filesRead = false;
  readBase = null;
  $("read-note").hidden = true;
  renderFiles();
}

function addFiles(list) {
  let why = "", added = 0;
  const bad = [], twice = []; // 받지 않는 형식, 이미 올린 파일(이름과 크기가 같은 것)은 모두 알린다
  for (const file of list) {
    const kind = kindOf(file.name), image = IMAGE_KINDS.includes(kind);
    if (!FILE_KINDS.includes(kind)) { bad.push(file.name); continue; }
    if (FILES.some((x) => x.file && x.name === file.name && x.file.size === file.size)) { twice.push(file.name); continue; }
    const no = file.size > 8 * 1024 * 1024 ? `파일 하나는 8MB까지 올릴 수 있어요: ${file.name}`
      : image && FILES.filter((x) => x.image).length >= 20 ? "이미지는 20장까지 올릴 수 있어요."
      : kind === "pdf" && FILES.some((x) => x.kind === "pdf") ? "PDF는 하나만 올릴 수 있어요." : "";
    if (no) { why ||= no; continue; }
    FILES.push({ name: file.name, kind, image, file, url: URL.createObjectURL(file) });
    filesTouched = true;
    filesRead = false;
    added += 1;
  }
  why = [bad.length ? `받지 않는 형식이에요: ${bad.join(", ")}. 이미지, 텍스트, md, pdf만 받아요.` : "", twice.length ? `이미 올린 파일이에요: ${twice.join(", ")}` : "", why].filter(Boolean).join(" ");
  if (why) newError(why); else clearError();
  renderFiles();
  // 글 파일(md·txt·pdf)만 올렸고 문제 글 칸이 비었으면 바로 읽어 온다(모델을 쓰지 않으니 기다릴 까닭이 없다). 이미지가 섞이면 단추로
  if (added && FILES.every((x) => TEXT_KINDS.includes(x.kind)) && !$("new-text").value.trim()) readFiles(!!why); // 받지 않은 파일 알림은 남긴다
}

const dataUrl = (blob) => new Promise((done, fail) => { const r = new FileReader(); r.onload = () => done(r.result); r.onerror = () => fail(r.error); r.readAsDataURL(blob); });
async function filesBody() { // 보관된 원본은 서버에서 다시 받아 같이 보낸다
  return Promise.all(FILES.map(async (x) => {
    let blob = x.file;
    if (!blob) { const r = await fetch(x.url); if (!r.ok) throw new Error(x.name); blob = await r.blob(); }
    return { name: x.name, data: await dataUrl(blob) };
  }));
}

/** 읽어 온 글에서 제목으로 쓸 줄. 머리말(문제, 문제 설명, Problem, 제한사항 …)은 건너뛰고 첫 줄을 본다:
    마크다운 제목(# …)이면 그것, 아니면 40자 이하이고 문장이 아닐 때(. ? 로 끝나거나 '입니다·합니다·주어집니다'로 끝나지 않을 때)만. 아니면 빈 글. */
let autoTitle = ""; // 본문 첫 줄에서 채운 제목(사용자가 고치지 않았으면 등록할 때 본문에서 그 줄을 뺀다)
/** 본문에서 제목으로 쓴 줄(과 바로 뒤 빈 줄)을 뺀다. */
function dropTitleLine(text, title) {
  const lines = String(text).split("\n"), at = lines.findIndex((raw) => raw.trim().replace(/^#{1,6}\s+/, "") === title);
  if (at < 0) return text;
  lines.splice(at, lines[at + 1] !== undefined && !lines[at + 1].trim() ? 2 : 1);
  return lines.join("\n").trim() ? lines.join("\n") : text;
}
function titleOf(text) {
  for (const raw of String(text).split("\n")) {
    const md = /^#{1,6}\s+(.+)$/.exec(raw.trim()), line = (md ? md[1] : raw).trim();
    if (!line || /^(문제|problem( description)?)$/i.test(line) || HEADING.test(line)) continue;
    return md || (line.length <= 40 && !/[.?]$/.test(line) && !/(입니다|합니다|주어집니다)$/.test(line)) ? line : "";
  }
  return "";
}

/** 읽은 글을 대조해 어긋난 곳(서버가 한 번 다시 읽고도 남은 것). 2걸음의 글 칸 바로 위에 목록으로. */
function showDoubts(list) {
  const rows = (list || []).map((d) => (d.note ? `${d.where}: ${d.note}` : `${d.where}: AI는 ${d.ai}, 글자 읽기는 ${d.ocr}`));
  $("doubts").innerHTML = rows.length ? `<span><strong>확인이 필요한 곳 ${rows.length}개</strong><ul>${rows.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></span>` : "";
  $("doubts").hidden = !rows.length;
}

/** 파일에서 글을 읽어 '문제 글' 칸을 바꾼다(사용자가 직접 적은 글은 같이 보내 엔진이 앞에 잇는다). 읽었으면 true. keep: 알림 줄을 지우지 않는다. */
async function readFiles(keep) {
  if (S.busy) return false; // 읽는 중이면 다시 부르지 않는다
  if (keep !== true) clearError();
  $("read-note").hidden = true; // '읽어 온 글이에요'는 읽은 뒤에만
  if (readBase === null) readBase = $("new-text").value;
  const wait = $("read-wait"); // 단추 옆 진행 줄(읽는 동안 단추와 올리는 자리는 data-model로 잠긴다)
  const r = await work("파일에서 글을 읽는 중…", "new", async () => {
    wait.innerHTML = `${DOTS}<span>파일에서 글을 읽는 중… <span class="secs" data-secs>0초</span></span>`;
    wait.hidden = false;
    let files;
    try { files = await filesBody(); } catch (e) { return { ok: false, error: { code: "files", message: "올린 파일을 불러오지 못했어요. 빼고 다시 올려 주세요." } }; }
    return api("/api/problems/read", { text: readBase, files, mode: $("new-mode").value });
  });
  wait.hidden = true;
  if (!r) return false;
  if (!r.ok) {
    const n = errorNote(r.error);
    newError(n.text, n.conn);
    say("");
    return false;
  }
  $("new-text").value = r.data.text;
  filesRead = true;
  renderFiles();
  if (!$("new-title").value.trim()) $("new-title").value = autoTitle = titleOf(r.data.text); // 제목 칸이 비었을 때만
  $("read-note").textContent = r.data.ocr === "ai_failed" ? "AI로 읽지 못한 장이 있어 이 기기의 글자 읽기로 읽었어요. 틀린 글자가 많을 수 있으니 원본과 견줘 고쳐 주세요." // 엔진이 주는 표시를 서버가 그대로 넘긴다
    : r.data.ocr ? "이 기기의 글자 읽기로 읽었어요. 틀린 글자가 많을 수 있으니 원본과 견줘 고쳐 주세요. AI를 연결하면 더 정확하게 읽어요."
    : "읽어 온 글이에요. 틀린 곳이 없는지 확인하고 고쳐 주세요.";
  showDoubts(r.data.doubts);
  readOcr = !!r.data.ocr;
  $("read-note").hidden = false;
  say("파일에서 글을 읽어 왔어요.");
  $("new-text").focus();
  findTable();
  return true;
}

function formMode(editing) {
  $("new-title-h").textContent = editing ? "문제 수정" : "내 문제 넣기";
  // 수정은 준비 없이 바로 저장한다. 등록 화면의 글을 그대로 쓰지 않는다
  $("new-lead").textContent = editing ? "바꿀 곳을 고친 뒤 저장해요." : "가진 문제를 글이나 사진으로 넣어 같은 방식으로 풀어요.";
  $("new-submit").textContent = editing ? "바꿔서 저장" : "등록하고 풀러 가기";
  document.querySelector('#wsteps li[data-wstep="3"]').lastChild.textContent = editing ? "저장" : "등록";
  $("new-title-note").hidden = editing; // '글의 첫 줄에서 채웠어요'는 새로 넣을 때만(수정의 제목은 저장해 둔 것이다)
  $("new-lang-field").hidden = editing; // 언어는 코드 화면에서 바꾼다
  $("new-mode").disabled = editing; // 푸는 방식은 등록할 때만 고른다(바꾸면 케이스와 코드가 모두 달라진다)
  $("new-mode-note").hidden = !editing;
  $("edit-confirm").hidden = $("case-fill-confirm").hidden = true;
  clearError();
}

/** 등록 화면의 언어 고르기. 처음(또는 등록·수정 뒤 비운 뒤)에는 마지막으로 고른 풀이 언어, 그다음에는 고르던 값을 둔다. */
function fillLangs() {
  const pick = $("new-lang"), was = pick._filled ? pick.value : (ACCOUNTS && ACCOUNTS.language) || "python";
  pick.innerHTML = langOptions(Object.keys(LANG));
  pick.value = was;
  pick._filled = true;
  const topic = $("new-theme"); // 주제: 정하지 않음 + 서버의 주제 15개(한 번만 채운다)
  if (ACCOUNTS && topic.options.length === 1) topic.insertAdjacentHTML("beforeend", ACCOUNTS.topics.map((x) => `<option value="${esc(x.key)}">${esc(x.name)}</option>`).join(""));
}

function showNew() {
  show("new");
  if (EDIT) { // 수정하던 값을 등록 화면에 남기지 않는다
    EDIT = null;
    emptyForm();
  }
  formMode(false);
  fillLangs();
  syncForm();
  findTable();
  setStep(WSTEP, false);
  if (!TOOLS) loadTools(false);
}

async function showEdit(pid) {
  show("new");
  formMode(true);
  setFiles([]);
  const r = await api("/api/state", { id: pid });
  if (S.view !== "new") return;
  if (!r.ok && r.error.code === "not_found") { // 지워진 문제의 수정 주소: 목록으로 보낸다
    sayNext("없는 문제예요. 지워졌거나 주소가 달라요.");
    return void (location.hash = "#/list");
  }
  if (!r.ok) return void newError(errorNote(r.error).text);
  const p = r.data.problem;
  const own = p.own_cases || p.examples; // 수정 화면은 숨긴 케이스도 값을 보여 준다
  $("new-float").checked = !!p.float_output;
  $("new-many").checked = !!p.many_answers;
  EDIT = { id: pid, text: p.text.trim(), cases: caseKey(own), flags: flagKey() };
  fillLangs();
  $("new-mode").value = p.mode || "function";
  $("new-title").value = p.title;
  $("new-theme").value = p.theme || "";
  $("new-level").value = p.level_by === "user" ? String(p.level) : ""; // 분석이 어림한 단계는 내가 고른 것이 아니다: 그대로 저장하면 고른 단계로 굳는다
  $("new-text").value = p.text;
  resetCases();
  findTable();
  setFiles(p.assets.map((a) => ({ name: a.name, kind: a.type, image: IMAGE_KINDS.includes(a.type), url: `/asset/${pid}/${a.n}`, asset: a }))); // 새로 올리지 않으면 그대로 둔다
  $("case-rows").innerHTML = "";
  for (const x of own) {
    addCaseRow();
    const [a, b, h] = caseCells($("case-rows").lastElementChild);
    a.value = x.input;
    b.value = x.expected;
    h.checked = !!x.hidden;
    showCall(a);
  }
  syncForm();
  setStep(2, false);
  $("new-title").focus();
}

let dupText = null; // 같은 글을 이미 넣었다고 알린 글. 그대로 한 번 더 누르면 넣는다
async function registerProblem(sure) {
  const cases = formCases(), editing = EDIT;
  formMode(!!editing);
  if (WSTEP !== 3) return void nextStep(); // 등록은 3걸음에서만(Ctrl+Enter로 앞 걸음에서 보내도 다음 걸음으로)
  if (editing && !sure && ($("new-text").value.trim() !== editing.text || caseKey(cases) !== editing.cases || flagKey() !== editing.flags)) { // 글이나 케이스(답 비교 표시 포함)를 바꾸면 지워질 것을 먼저 알린다
    const what = [$("new-text").value.trim() !== editing.text && "문제 글", caseKey(cases) !== editing.cases && "케이스", flagKey() !== editing.flags && "답 비교 표시"].filter(Boolean);
    const textOnly = what.length === 1 && what[0] === "문제 글"; // 글이 바뀌면 늘 지운다. 케이스·답 비교만 바뀌면 튜터의 풀이가 새 케이스로 통과하지 못할 때만
    $("edit-confirm-text").textContent = `${what.join(", ")}${textOnly ? "을" : "를"} 바꾸면 튜터와 나눈 대화와 블록 진행이 ${what[0] === "문제 글" ? "지워져요" : "지워질 수 있어요"}. 제출 기록과 코드는 남아요.`;
    $("edit-confirm").hidden = false;
    return $("edit-no").focus();
  }
  const text = !editing && autoTitle && $("new-title").value === autoTitle ? dropTitleLine($("new-text").value, autoTitle) : $("new-text").value;
  const typed = $("case-names-field").hidden ? [] : $("case-names").value.split(",").map((x) => x.trim()).filter(Boolean);
  if (typed.length) { // 직접 적은 인자 이름: 이름 꼴이고 서로 다르고 넣을 값의 수와 같아야 한다(어긋나면 말없이 버리지 않고 알린다)
    let count = null;
    try { count = JSON.parse((cases.find((x) => x.input.trim()) || {}).input).length; } catch (e) { /* 넣을 값이 틀렸으면 서버가 그 칸을 짚는다 */ }
    const wrong = typed.some((x) => !/^[A-Za-z_][A-Za-z0-9_]*$/.test(x)) || new Set(typed).size !== typed.length, uneven = count !== null && count !== typed.length;
    if (wrong || uneven) setStep(2, false); // 그 칸이 있는 걸음으로 돌아가 칸 아래에 알린다
    if (wrong) return newError("인자 이름은 영문자·숫자·밑줄로, 서로 다르게 적어 주세요. 예: numbers, k", false, "case-names");
    if (uneven) return newError(`인자 이름이 ${typed.length}개인데 넣을 값은 ${count}개예요. 수를 맞춰 주세요.`, false, "case-names");
  }
  const names = NAMES || (typed.length ? typed : null);
  const body = { title: $("new-title").value, text, theme: $("new-theme").value, level: Number($("new-level").value) || 0, cases, ...(names ? { names } : {}), ...answerFlags() };
  const r = await work(editing ? "고친 내용을 저장하는 중…" : "문제를 등록하는 중…", "new", async () => {
    try {
      if (editing ? filesTouched : FILES.length) body.files = await filesBody(); // 수정에서 파일을 건드리지 않았으면 보내지 않는다(원본 그대로)
    } catch (e) { return { ok: false, error: { code: "files", message: "올린 파일을 불러오지 못했어요. 빼고 다시 올려 주세요." } }; }
    return editing ? api("/api/problems/edit", { ...body, id: editing.id }) : api("/api/problems/new", { ...body, language: $("new-lang").value, mode: $("new-mode").value, ...(dupText === text ? { again: true } : {}) });
  });
  if (!r) return;
  dupText = !r.ok && r.error.code === "duplicate" ? text : null;
  if (!r.ok) { // 서버가 짚은 칸이 있는 걸음으로 돌아가 그 칸 아래에 알린다
    const n = errorNote(r.error);
    const field = { title: "new-title", text: "new-text", language: "new-lang", theme: "new-theme", mode: "new-mode", level: "new-level", cases: "case-input-1" }[r.error.field] || r.error.field;
    if (field && $(field)) { setStep(2, false); if ($("new-more").contains($(field))) $("new-more").open = true; }
    newError(n.text, n.conn, field && $(field) ? field : null);
    return say("");
  }
  sayNext(editing ? "고친 내용을 저장했어요." : "문제를 등록했어요.");
  EDIT = null;
  emptyForm(); // 등록하면 초안은 비운다
  WSTEP = 1;
  S.pid = null; // 고친 문항을 다시 열 때 예전 글을 쓰지 않게 새로 받는다
  location.hash = `#/p/${r.data.id}`;
}

/* 05-6 원본 보기: 이미지는 창에 맞춰, PDF는 내장 보기, md·txt는 글 그대로 */
async function openAsset(n) {
  const a = S.problem.assets.find((x) => x.n === n), url = `/asset/${S.pid}/${n}`, box = $("asset"), body = $("asset-body");
  $("asset-title").textContent = `원본 ${n}`;
  $("asset-name").textContent = a.name;
  body.innerHTML = "";
  if (IMAGE_KINDS.includes(a.type)) body.append(Object.assign(document.createElement("img"), { src: url, alt: a.name }));
  else if (a.type === "pdf") body.append(Object.assign(document.createElement("iframe"), { src: url, title: a.name }));
  else body.append(Object.assign(document.createElement("pre"), { textContent: "불러오는 중…" }));
  if (!box.open) box.showModal ? box.showModal() : box.setAttribute("open", "");
  $("asset-title").focus();
  const pre = body.querySelector("pre");
  if (pre) { const r = await fetch(url).catch(() => null); pre.textContent = r && r.ok ? await r.text() : "원본을 불러오지 못했어요."; }
}
const closeAsset = () => { const box = $("asset"); box.close ? box.close() : box.removeAttribute("open"); };

/* ── 05–08 코드 화면 ── */
function clearProblem(pid) {
  Object.assign(S, { pid, problem: null, session: null, hasFeedback: false, mode: null, choosing: false, soloOpen: null, talk: "chair", codeTab: "direct", blockCode: {}, result: null,
    quote: null, sending: null, debug: null, note: {}, codeNote: "", fb: null, solo: null, langWant: null, codeAsk: null, fillAsk: null, prepAt: 0, keptNote: false, keptSeen: false, nextUp: null, pullThenRun: false });
  for (const id of ["code", "say", "fq-text", "debug-say", "run-input"]) $(id).value = "";
  for (const id of ["p-title", "p-text", "blocks", "chat-log", "explain-box", "start-box", "result", "solo-box"]) $(id).innerHTML = "";
  for (const id of ["result", "debug-sheet", "composer", "fq-composer", "chat-log", "explain-box", "old-feedback", "solo-box", "lang-confirm"]) $(id).hidden = true;
  $("code")._seen = "";
  say(""); // 앞 문제의 상태 문구('튜터가 블록 코드를 봤어요')를 남기지 않는다
  $("reset-confirm").hidden = $("del-confirm").hidden = true;
  $("reset").hidden = $("p-edit").hidden = $("p-delete").hidden = false;
  $("code-error").hidden = true;
  $("more").open = false;
}

/* 고른 방식은 문제마다 이 기기에 기억한다(서버 세션에는 방식이 따로 없다) */
const wayKey = (pid) => `algoblock.way.${pid}`;
const savedWay = (pid) => { try { return localStorage.getItem(wayKey(pid)); } catch (e) { return null; } };
const saveWay = (pid, way) => { try { localStorage.setItem(wayKey(pid), way); } catch (e) { /* 저장하지 못해도 이번에는 그 방식으로 */ } };
const tutorWay = (mode) => mode === "chair" || mode === "guide";

async function showCode(pid) {
  show("code");
  if (S.pid !== pid) clearProblem(pid);
  render();
  await loadState(true);
  if (S.view === "code" && !S.mode && document.querySelector('[data-way="solo"]')) document.querySelector('[data-way="solo"]').focus(); // 고르기 전: 혼자 풀기에 초점
}

async function loadState(open) {
  const pid = S.pid, asked = S.talk;
  const r = await api("/api/state", { id: pid, mode: asked, open: !!open });
  if (S.pid !== pid) return;
  $("code-error").hidden = r.ok;
  if (!r.ok && r.error.code === "not_found") { // 지워진(없는) 문제: 목록으로 보낸다
    S.pid = null;
    sayNext("없는 문제예요. 지워졌거나 주소가 달라요.");
    return void (location.hash = "#/list");
  }
  if (!r.ok) return void ($("code-error").textContent = errorNote(r.error).text);
  applyState(r.data);
  if (S.talk !== asked && S.pid === pid) return loadState(); // 처음 열며 그 문제의 방식이 정해졌다: 서버가 이름을 가리는 것은 방식마다 달라, 정해진 방식으로 다시 받는다
}

/** 서버가 준 문제 상태를 화면 상태로 옮긴다. 처음 받았을 때만 코드 칸과 문제 글을 채운다(적던 글을 덮지 않게). */
function applyState(data) {
  const first = !S.problem;
  S.problem = data.problem;
  TOOLS = data.problem.tools;
  S.session = data.session;
  S.hasFeedback = data.has_feedback;
  S.ownWay = data.own_way === true; // '끝까지 내 방식으로 쓰기'(서버가 문항마다 남긴다: 다시 열어도 그대로)
  if (first) {
    const p = S.problem;
    $("code").value = $("code")._seen = p.code || p.starter || ""; // 아직 쓴 코드가 없으면 그 언어의 시작 코드(함수 틀)
    S.blockCode = data.blocks || {};
    $("p-text").innerHTML = rich(p.text, true, p.mode === "program") + (p.assets.length ? `<p class="assets"><span class="muted">원본</span>${p.assets.map((a) => `<button type="button" class="btn small" data-asset="${a.n}" title="${esc(a.name)}">원본 ${a.n}</button>`).join("")}</p>` : "");
    document.title = `${p.title} · AlgoBlock`;
    S.solo = { shown: [], seen: p.study.hints_seen, total: p.study.hints_total, sol: null, ask: false, note: null };
    if (p.study.hints_seen) loadHints(true); // 전에 본 힌트를 다시 보여 준다(새 힌트를 열지 않는다)
    if (p.study.has_guide && p.study.passed_now) loadSolution(false); // 이번 풀이에서 통과한 문제는 실전 신호를 준비해 둔다('처음부터' 뒤에는 열 때만 보인다)
    // 방식: 기억한 것, 없으면 대화가 있는 쪽(마지막 말이 늦은 쪽), 없으면 고르기 전(어떻게 풀까요?)
    const lastAt = (chat) => (chat[chat.length - 1] || {}).at || "", sess = data.session;
    let way = savedWay(S.pid) || (sess.guide.length || sess.chair.length ? (lastAt(sess.guide) > lastAt(sess.chair) ? "guide" : "chair") : null);
    if (tutorWay(way) && !connected()) way = "solo";
    S.mode = way;
    if (tutorWay(way)) { S.talk = way; S.codeTab = "blocks"; if (!codeEmpty()) S.keptNote = S.keptSeen = true; }
  }
  S.solo.total = S.problem.study.hints_total; // 튜터가 뒤에서 계획을 다 만들면 힌트가 생긴다(새로 고침하지 않아도)
  S.prepAt = S.problem.preparing ? S.prepAt || Date.now() : 0; // 준비 진행 줄에 지난 초를 보여 준다(새 준비는 0초부터)
  render();
  clearTimeout(prepTimer);
  if (S.problem.preparing && connected()) { // 튜터가 뒤에서 풀이 순서를 준비하는 중: 3초마다 다시 보고, 끝나면 표시를 걷는다(문제 화면을 떠나면 멈춘다)
    const pid = S.pid;
    prepTimer = setTimeout(() => { if (S.view === "code" && S.pid === pid) loadState(); }, 3000);
  }
}
let prepTimer = null;

/** 코드 전체 칸이 비었는가(시작 코드만 있는 것도 빈 것으로 본다). */
const codeEmpty = () => { const text = $("code").value.trim(); return !text || text === ((S.problem && S.problem.starter) || "").trim(); };

function renderCode() {
  const p = S.problem;
  if (!p || !S.session) return;
  $("p-title").textContent = p.title;
  if (!connected() && S.mode && S.mode !== "solo") S.mode = "solo"; // 모델이 없으면 혼자 풀기뿐이다(고르기 전이면 고르는 칸에서 까닭을 말한다)
  if (!connected()) S.codeTab = "direct"; // 블록은 튜터와 쌓는 것이라, 모델이 없으면 코드 전체만 보여 준다
  $("p-badges").innerHTML = lvBadge(p.level, p.level_by === "analysis") + themeChip(p.theme, p.theme_name) + (p.sample ? "" : verifiedBadge(p)) + tagChips(p.tags);
  renderCheckLine(p);
  $("p-own").hidden = p.sample; // 내가 등록한 문제만 고치고 지운다
  const picker = $("p-lang-select"), many = p.languages.length > 1, key = p.languages.join(",") + JSON.stringify(TOOLS);
  $("p-lang").hidden = many;
  picker.hidden = !many;
  $("p-lang").textContent = LANG[p.language] || p.language;
  if (picker._key !== key) { picker._key = key; picker.innerHTML = langOptions(p.languages); }
  if (!S.langWant) picker.value = p.language;
  picker.disabled = !!S.busy;
  $("lang-confirm").hidden = !S.langWant;
  $("code-tools").hidden = !!S.codeAsk;
  $("code-confirm").hidden = !S.codeAsk;
  $("cp-save").disabled = $("code-clear").disabled = !!S.busy;
  $("cp-restore").disabled = !!S.busy || !p.checkpoint_at; // 남긴 체크포인트가 없으면 되돌릴 것이 없다
  if (S.codeAsk) { // 초기화의 단추는 '시작 코드로'(체크포인트 '되돌리기'와 헷갈리지 않게)
    const back = S.codeAsk === "clear" && S.codeTab === "direct" && p.starter; // 코드 전체 칸은 시작 코드로 돌아간다
    $("code-confirm-text").textContent = S.codeAsk === "restore" ? `마지막 체크포인트(${when(p.checkpoint_at)})로 되돌릴까요? 지금 코드는 사라져요.`
      : S.codeAsk === "pull" ? (S.pullNudge ? "블록 칸의 코드를 아직 모으지 않았어요 — 모을까요? ‘코드 전체’ 칸의 코드는 모은 코드로 바뀌어요." : "‘코드 전체’ 칸의 코드를 블록을 모은 코드로 바꿀까요?") : back ? "코드 칸을 시작 코드로 되돌릴까요?" : "코드 칸을 비울까요?";
    $("code-yes").textContent = S.codeAsk === "restore" ? "되돌리기" : S.codeAsk === "pull" ? (S.pullNudge ? "모으기" : "바꾸기") : back ? "시작 코드로" : "비우기";
  }
  $("p-count").textContent = p.submitted ? `통과 ${p.passed} · 제출 ${p.submitted}` : "";
  $("old-feedback").hidden = !S.hasFeedback;
  renderBlocks();
  renderCodePane();
  renderResult();
  syncGutter(); // 결과 칸을 그린 뒤(편집기 높이가 정해진 뒤)에 짚은 줄을 맞춘다
  renderTutor();
  renderDebug();
  const stage = nextAction();
  renderSteps(stage, applyPrimary(stage));
}

let prepAsking = false; // 다시 준비 요청 중(두 번 눌러 겹치지 않게)
async function prepAgain() {
  if (prepAsking) return;
  prepAsking = true;
  document.querySelectorAll("#prep-again, #prep-again-top").forEach((el) => { el.disabled = true; });
  try { S.note.start = null; S.problem.prepare_failed = false; S.prepAt = 0; await loadState(true); say(S.problem.preparing ? "튜터가 풀이 순서를 다시 준비해요." : ""); } finally { prepAsking = false; }
}

/** 등록한 문제의 준비·검증 한 줄: "풀이 준비 중 · 숨은 테스트 n개 만듦 · 검증: 예시와 대조 모두 통과" */
function renderCheckLine(p) {
  const c = p.check || {}, made = (Number(c.hidden) || 0) + (Number(c.efficiency) || 0);
  const parts = p.sample ? [] : [p.preparing ? "풀이 준비 중" : "", made ? `숨은 테스트 ${made}개 만듦` : "", p.verified_name ? `검증: ${p.verified_name}` : "", c.why && p.verified !== "all" ? String(c.why) : "", p.prepare_failed && !p.preparing ? "튜터가 풀이 순서를 준비하지 못했어요." : ""].filter(Boolean).map(esc); // 준비가 실패로 끝났으면 말하고 다시 준비하는 길을 둔다
  if (p.preparing) parts[0] += ` <span class="secs" data-since="${S.prepAt}">${since(S.prepAt)}초</span> · 보통 1분 안팎`; // 다른 기다림 표시처럼 지난 초
  $("p-check").innerHTML = parts.length ? `${p.preparing ? DOTS : ""}<span>${parts.join(" · ")}</span>${p.prepare_failed && !p.preparing ? ' <button type="button" class="btn small" id="prep-again-top" data-model>다시 준비</button>' : ""}` : "";
  $("p-check").hidden = !parts.length;
}

/** 상태마다 주 동작 하나(파란 채움): 그 단추에만 primary를 붙이고 나머지에서는 뗀다. 붙인 단추를 돌려준다. */
const PRIMARY = { choose: '[data-way="solo"]', run: "#run", submit: "#submit", compose: "#compose-run", start: "#start", talk: "#send", follow: "#fq-send",
  check: ".block.is-current [data-check]", debug: "#debug-send", find: "#debug-start", hint: "#result-hint", next: "#result-next", feedback: "#to-feedback" };
function applyPrimary(stage) {
  document.querySelectorAll("#view-code .primary").forEach((el) => el.classList.remove("primary"));
  const shown = (sel) => { const el = document.querySelector(`#view-code ${sel}`); return el && !el.closest("[hidden]") && !el.disabled ? el : null; };
  const el = shown(PRIMARY[stage]) || shown("#run") || shown("#submit");
  if (el) el.classList.add("primary");
  return el;
}

/** 풀이 순서 네 걸음 중 지금 어디인지만 짚고, 그 걸음의 주 동작 이름을 곁에 쓴다(앞 걸음을 끝냈다고 표시하지 않는다: 건너뛰고 올 수도 있다). */
const STEPS = ["생각하기", "코드 쓰기", "제출·고치기", "돌아보기"];
const STEP_OF = { check: 1, choose: 0, start: 0, talk: 0, follow: 0, compose: 1, run: 1, submit: 2, find: 2, hint: 2, debug: 2, feedback: 3, next: 3, review: 3 };
function renderSteps(stage, el) {
  const at = STEP_OF[stage] ?? 1, doing = stage === "choose" ? "어떻게 풀지 고르기" : stage === "review" ? "통과한 문제" : el ? el.textContent.trim() : "";
  $("steps").innerHTML = STEPS.map((name, i) => `<li${i === at ? ' class="now" aria-current="step"' : ""}><span class="step-no" aria-hidden="true">${i + 1}</span>${name}${i === at && doing ? `<span class="step-do"> · ${esc(doing)}</span>` : ""}</li>`).join("");
}

/** 답은 맞고 큰 입력에서만 걸렸다. */
const slowOnlyOf = (r) => !r.ok && !r.run && r.cases.length > 0 && !!r.score && r.score.accuracy[0] === r.score.accuracy[1] && r.score.efficiency[1] > 0;
/** '끝까지 내 방식으로 쓰기'가 지금 보이는 튜터 차례(가이드)에 켜져 있다. */
const ownWayOn = () => !!S.ownWay && S.mode === "guide" && S.talk === "guide";
/** 튜터 블록을 다 열고(의자는 다 찾고) 빈 칸이 없다: 모아서 실행할 때. */
const blocksReady = () => S.session.blocks.length > 0 && (S.mode === "chair" ? allFound() : S.session.open_count >= S.session.blocks.length || passedAloneAt() >= 0) && !emptyBlocks().length;

/** 지금 가장 먼저 할 일 하나. 그 단추만 채워서 보여 준다. */
function nextAction() {
  const s = S.session, r = S.result, ai = connected();
  if (S.debug && S.debug.open && !S.debug.passed) return "debug";
  if (S.quote) return "follow";
  if (!S.mode || S.choosing) return "choose";
  if (r && r.run && !r.own && !r.ok && !r.alert && !r.stale && r.cases.length && ai && tutorWay(S.mode) && !slowOnlyOf(r)) return "find"; // 튜터 방식에서 예시가 틀렸다
  if (r && !r.alert && !r.stale && !r.run && !r.own && r.cases.length) { // 제출 결과 바로 아래의 다음 할 일
    if (r.ok) return "next";
    if (ai && !slowOnlyOf(r)) return "find";
    if (S.solo && S.solo.total && !(S.mode === "solo" && S.soloOpen === "hint")) return "hint"; // 힌트를 이미 열었으면 다음은 코드를 고쳐 실행
    if (ai) return "feedback";
  }
  if (!r && S.problem.passed > 0) return "review"; // 통과한 문제를 다시 열었다: 쓰는 걸음이 아니라 돌아보는 걸음이다
  if (tutorWay(S.mode) || S.mode === "explain") {
    if (S.mode === "explain" ? !s.explain : !s[S.mode].length) return "start";
    if (S.mode === "guide" && ownWayOn()) return "compose"; // 끝까지 내 방식으로 쓰기: 블록마다 확인하지 않고 모아서 실행으로 확인한다
    if (S.mode === "guide" && (s.guide.findLast((m) => m.role === "service") || {}).move === "write") return "check"; // 튜터의 마지막 말이 코드를 적으라는 것: 다음은 다시 보내기가 아니라 그 블록의 코드 확인
    if (tutorWay(S.mode) && !blocksReady()) return "talk";
    if (tutorWay(S.mode) && (S.codeTab === "blocks" || codeEmpty())) return "compose";
  }
  if (r && r.run && r.ok && !r.stale) return "submit";
  return S.problem.cases && S.problem.cases.example ? "run" : "submit";
}

const allFound = () => S.mode === "chair" && S.session.blocks.length > 0 && S.session.blocks.every((b) => b.name);

function blockState(b, i) {
  const current = S.session.open_count - 1;
  if (i > current) return "locked";
  if (i < current) return "found";
  return S.talk === "chair" && b.name ? "found" : "current"; // 의자는 지금 블록 이름이 답이라 찾기 전에는 가린다
}

/** 블록 칸에 사람이(또는 도구가) 넣은 값을 상태로 옮긴다. 그리기 전에 부르면 적던 글이 남는다. */
function harvest() {
  document.querySelectorAll("#blocks textarea[data-block]").forEach((ta) => {
    if (ta.value === ta._seen) return;
    ta._seen = ta.value;
    S.blockCode[ta.dataset.block] = { code: ta.value, by: "me" };
    saveBlocksSoon();
  });
}

/** 칸 글이 마지막으로 확인받은 글과 같은가. */
const sameCode = (b, saved) => typeof b.checked === "string" && (saved.code || "").trim() === b.checked.trim();
/** 블록 상태: 글과 모양으로 보인다(원의 색만으로 가르지 않는다). 칸이 비면 그리지 않는다.
    pass: 확인받아 통과, wait: 확인 전(확인받지 않았거나 글을 고쳤다), skip: 확인하지 않고 넘어감, stale: 앞 블록이 바뀌어 통과를 물렸다, fail: 마지막 확인이 통과하지 못했다. */
function blockStatus(b, saved) {
  if (!sameCode(b, saved)) return "wait";
  const line = saved.line || {};
  if (b.verdict === "Y") return "pass";
  if (line.skipped) return "skip"; // '이대로 넘어가기'로 둔 블록: 그냥 확인 전과 구별한다
  if ((b.verdict === "N" && !line.unsure) || line.ok === false) return "fail"; // '?'인데 내가 방금 다시 확인해 실패했다. 실행이 뒷받침하지 못한 실패(unsure)는 '확인 전'이다
  return line.withdrawn && !(S.problem && S.problem.passed > 0) ? "stale" : "wait"; // 통과한 문제에는 ‘앞 블록이 바뀌었어요’를 남기지 않는다
}
const STATUS = {
  get pass() { return `${ico("i-check")}${S.problem && S.problem.cases && S.problem.cases.accuracy === 0 ? "예시 통과" : "통과"}`; }, // 숨은 테스트가 없으면 공개 예시로만 돌려 본 통과다
  wait: `${ico("i-info")}확인 전`, skip: `${ico("i-info")}넘어감 · 확인 전`, stale: `${ico("i-info")}확인 전 · 앞 블록이 바뀌었어요`, fail: `${ico("i-x")}이어지지 않아요`,
};

function renderBlocks() {
  harvest();
  const s = S.session, list = $("blocks");
  if (!s.blocks.length) {
    list.innerHTML = '<li class="empty"><strong>아직 블록이 없어요</strong><span>튜터와 시작하면 풀이 순서대로 블록이 하나씩 놓여요.</span></li>';
  } else if (!s[S.talk].length) { // 시작 전에는 블록 칸을 열어 두지 않는다(오른쪽 시작 단추와 시선이 갈렸다)
    list.innerHTML = '<li class="empty"><span>튜터를 시작하면 블록이 하나씩 열려요</span></li>';
  } else {
    list.innerHTML = s.blocks.map((b, i) => {
      const state = blockState(b, i), n = i + 1;
      if (state === "locked") {
        return `<li class="block is-locked"><span class="no" aria-hidden="true">${n}</span><div class="block-head"><span class="sr-only">블록 ${n}, 아직 열리지 않음.</span>${kindChip(b.kind)}<span class="lock">${ico("i-lock")}</span></div></li>`;
      }
      const saved = S.blockCode[b.id] || { code: "", by: "" };
      const current = state === "current";
      const empty = !saved.code.trim();
      const cell = !current || !empty || S.talk === "guide";
      const rows = Math.min(10, Math.max(2, saved.code.split("\n").length));
      const check = showCheck(b, state, current), st = empty ? "" : blockStatus(b, saved), line = saved.line || {};
      const result = st && st !== "pass" && sameCode(b, saved) && line.text ? `<p class="block-result is-${line.ok === false ? "fail" : "wait"}">${inline(line.text)}${line.skipped ? "" : ' <span class="muted">자세한 말은 오른쪽 튜터의 말에 있어요.</span>'}</p>` : "";
      const skip = current && S.talk === "guide" && (st === "fail" || st === "wait") && sameCode(b, saved) && !!line.text; // 마지막 확인이 통과가 아니면 갇히지 않게 넘어갈 길을 준다
      return `<li class="block is-${state}${st ? ` st-${st}` : ""}"${current ? ' aria-current="step"' : ""}>
        <span class="no" aria-hidden="true">${n}</span>
        <div class="block-head"><span class="sr-only">블록 ${n}.</span>${kindChip(b.kind)}<span class="block-name">${esc(b.name || "지금 찾는 블록")}</span>
          ${st ? `<span class="st">${saved.by === "tutor" ? '<span class="by">튜터가 채움</span>' : ""}<span class="st-chip">${STATUS[st]}</span></span>` : ""}</div>
        ${current && KIND[b.kind] ? `<p class="kind-desc">${esc(KIND[b.kind][1])}</p>` : ""}
        ${cell ? `<textarea class="codey" data-block="${esc(b.id)}" rows="${rows}" aria-label="블록 ${n} 코드" spellcheck="false" autocapitalize="off" wrap="off" placeholder="이 블록의 코드 (들여쓰기는 쓴 그대로 모여요)">${esc(saved.code)}</textarea>` : ""}
        ${result}
        <div class="block-actions">
          ${check ? `<button type="button" class="btn small" data-check="${esc(b.id)}" data-model${current ? "" : ` aria-label="블록 ${n} 코드 확인"`}>블록 코드 확인</button>` : ""}
          ${skip ? `<button type="button" class="btn quiet small" data-skip="${esc(b.id)}">이대로 넘어가기</button>` : ""}
          ${skip && !S.ownWay ? `<button type="button" class="btn quiet small" data-own="${esc(b.id)}" title="이 블록은 넘어가고 남은 블록을 모두 열어요. 블록마다 확인하지 않고, 다 쓴 뒤 ‘모아서 실행’으로 확인해요">끝까지 내 방식으로 쓰기</button>` : ""}
          ${S.fillAsk === b.id ? `<span class="confirm"><span>적은 코드를 튜터의 코드로 바꿀까요?</span><button type="button" class="btn danger small" data-fill-yes="${esc(b.id)}" data-model>바꾸기</button><button type="button" class="btn quiet small" data-fill-no="${esc(b.id)}">그대로 두기</button></span>`
    : `<button type="button" class="btn quiet small" data-fill="${esc(b.id)}" data-model${current ? "" : ` aria-label="블록 ${n} 채우기"`}>이 블록 채우기</button>`}
        </div>
      </li>`;
    }).join("");
    list.querySelectorAll("textarea").forEach((ta) => { ta._seen = ta.value; });
  }
  const own = ownWayOn() ? `<div class="note" role="status">내 방식으로 끝까지 쓰는 중이에요. 블록마다 확인하지 않고, 다 쓴 뒤 ‘모아서 실행’으로 확인해요. <button type="button" class="btn quiet small" data-own-off>튜터 차례로 돌아가기</button></div>` : "";
  $("blocks-note").innerHTML = (S.busy && S.busy.where === "blocks" ? `<div class="note">${waitLine("blocks")}</div>` : "") + own + noteHtml(S.note.blocks);
}

/** '블록 코드 확인' 단추를 보이는가: 가이드의 지금 블록, 의자에서 찾은 블록, 가이드의 앞 블록 가운데 칸 글이 저장된 글과 다르거나 '확인 전'(stale)인 것.
    고쳐도 곧바로 단추가 보이지 않았고, 실패한 다시 확인 뒤에는 단추가 사라졌다. */
function showCheck(b, state, current) {
  if (ownWayOn()) return false; // 끝까지 내 방식으로 쓰는 동안은 블록마다 확인하지 않는다
  const s = S.session, saved = S.blockCode[b.id] || { code: "" };
  // 대화로 찾은 앞 블록(확인 기록이 없다)도 코드를 적으면 단추가 보인다
  const edited = state === "found" && S.mode === "guide" && !!saved.code.trim() && (!sameCode(b, saved) || b.verdict !== "Y");
  return (current && S.mode === "guide" && s.guide.length > 0) || edited || (state === "found" && S.mode === "chair" && S.talk === "chair" && s.chair.length > 0);
}
/** 입력 때 그 블록의 단추만 다시 그린다(칸을 다시 그리지 않아 커서가 그대로다). */
function syncCheck(ta) {
  const i = S.session.blocks.findIndex((b) => b.id === ta.dataset.block);
  if (i < 0) return;
  const b = S.session.blocks[i], state = blockState(b, i), box = ta.closest("li").querySelector(".block-actions");
  const btn = box.querySelector("[data-check]"), want = showCheck(b, state, state === "current");
  if (want && !btn) box.insertAdjacentHTML("afterbegin", `<button type="button" class="btn small" data-check="${esc(b.id)}" data-model aria-label="블록 ${i + 1} 코드 확인">블록 코드 확인</button>`);
  if (!want && btn) btn.remove();
  // 상태 칩과 결과 줄도 지금 글에 맞춘다(고친 글은 '확인 전', 지난 결과 줄은 걷는다)
  const li = ta.closest("li"), now = { ...(S.blockCode[b.id] || {}), code: ta.value }, st = ta.value.trim() ? blockStatus(b, now) : "", chip = li.querySelector(".st-chip");
  if (chip && st) chip.innerHTML = STATUS[st];
  li.classList.remove("st-pass", "st-wait", "st-skip", "st-stale", "st-fail");
  if (st) li.classList.add(`st-${st}`);
  if (!sameCode(b, now)) { const res = li.querySelector(".block-result"); if (res) res.remove(); }
}

/** 블록 칸의 코드를 실행되는 한 파일의 조각으로 모은다 [[블록 순번(0부터), 글], …]. 모으기는 서버 한 곳(/api/compose)에서 한다:
    블록 코드 확인이 잇는 것과 같은 함수로 만들어 '확인이 돌린 프로그램'과 '모은 코드'가 같은 글이 된다.
    요청이 실패하면 알림을 남기고 null(모으지 않는다). */
async function composedParts() {
  harvest();
  const r = await api("/api/compose", { id: S.pid, mode: S.talk, blocks: S.blockCode });
  if (!r.ok) { S.codeNote = errorNote(r.error).text; render(); return null; }
  return r.data.parts;
}

/** 문자열·문자·주석 밖의 중괄호를 차례로: 여는 것 1, 닫는 것 -1. 문자 리터럴('{', '\'')만 건너뛰고 Rust 수명('a)은 글자로 본다. */
function braceMarks(text) {
  const out = [];
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i], two = text.slice(i, i + 2);
    if (two === "//") { i = text.indexOf("\n", i); if (i < 0) break; }
    else if (two === "/*") { i = text.indexOf("*/", i + 2); if (i < 0) break; i += 1; }
    else if (c === '"' || c === "`") { for (i += 1; i < text.length && text[i] !== c; i += 1) if (text[i] === "\\" && c === '"') i += 1; }
    else if (c === "'") { const m = /^'(?:\\.[^'\n]{0,5}|[^\\'\n])'/.exec(text.slice(i, i + 10)); if (m) i += m[0].length - 1; }
    else if (c === "{" || c === "}") out.push(c === "{" ? 1 : -1);
  }
  return out;
}
const BRACE_LANGS = new Set(["java", "kotlin", "cpp", "go", "rust", "javascript"]);
/** 모은 코드의 중괄호 수가 맞지 않으면 살펴볼 블록 번호(1부터): 처음으로 닫는 괄호가 더 많아지는 블록, 없으면 마지막으로 열린 채 남은 블록. 맞으면(또는 Python이면) 0. */
function braceGap(composedList) {
  if (!BRACE_LANGS.has(S.problem.language)) return 0;
  const parts = composedList.map(([i, text]) => [i, braceMarks(text)]);
  if (!parts.reduce((n, [, marks]) => n + marks.reduce((a, b) => a + b, 0), 0)) return 0;
  const open = [];
  for (const [i, marks] of parts) for (const m of marks) {
    if (m > 0) open.push(i);
    else if (!open.length) return i + 1;
    else open.pop();
  }
  return open.length ? open[open.length - 1] + 1 : 0;
}
/** 블록을 모은 뒤: 중괄호 짝이 맞지 않으면 알린다(모은 코드는 그대로 둔다). */
function warnBraces(parts) {
  const n = braceGap(parts || []), box = $("code-error");
  if (n) box.textContent = `모은 코드의 중괄호 짝이 맞지 않아요. 블록 ${n}의 코드에서 여는 괄호와 닫는 괄호를 확인해 주세요.`;
  if (n || box.textContent.startsWith("모은 코드의 중괄호")) box.hidden = !n; // 다시 모아 맞으면 지난 알림을 걷는다
}

/** 튜터가 '지금까지 쓴 코드만으로 이미 통과해요'(엔진 ALONE_OK)라 말한 마지막 확인의 블록 순번(0부터). 그 뒤 블록은 건너뛰어도 된다고 했다. 없으면 -1. */
function passedAloneAt() {
  let at = -1;
  for (const chat of [S.session.guide, S.session.chair]) chat.forEach((m, n) => {
    if (m.role === "service" && m.text.startsWith("지금까지 쓴 코드만으로 이미 통과해요") && n > 0 && chat[n - 1].role === "user") at = Math.max(at, chat[n - 1].block_index);
  });
  return at;
}

/** 열린 블록 가운데 코드 칸이 빈 것의 순번(0부터). 잠긴 블록과, 의자에서 아직 찾지 못한 지금 블록(칸이 없다), 튜터가 건너뛰어도 된다고 한 블록(passedAloneAt 뒤)은 보지 않는다. */
function emptyBlocks() {
  harvest();
  if (!S.session) return [];
  const alone = passedAloneAt();
  return S.session.blocks.map((b, i) => [b, i, blockState(b, i)])
    .filter(([b, i, state]) => state !== "locked" && !(state === "current" && S.talk === "chair") && !(alone >= 0 && i > alone) && !((S.blockCode[b.id] || {}).code || "").trim()).map(([, i]) => i);
}
const gapText = (gaps) => `블록 ${gaps.map((i) => i + 1).join(", ")}의 코드 칸이 비어 있어요. 직접 적거나 ‘이 블록 채우기’를 눌러 주세요.`;

/** 빈 블록이 있으면 모으지 않고 블록 탭에서 알린다(첫 빈 칸으로 스크롤하고 초점). 알렸으면 true. */
function warnGaps() {
  const gaps = emptyBlocks();
  if (!gaps.length) return false;
  S.codeTab = "blocks";
  S.note.blocks = { type: "warn", text: gapText(gaps), gap: true };
  render();
  const ta = document.querySelector(`#blocks textarea[data-block="${CSS.escape(S.session.blocks[gaps[0]].id)}"]`);
  if (ta) { ta.scrollIntoView({ block: "center" }); ta.focus(); }
  return true;
}

/** 코드 전체 칸이 비어 있으면(시작 코드뿐이어도) 지금까지의 블록을 한 파일로 보여 준다. 열린 블록에 빈 칸이 있으면 모으지 않고 블록 탭에서 알린다(알렸으면 true).
    how: "tab"(사용자가 탭을 눌렀다. 알린 뒤 한 번 더 누르면 모으지 않고 옮긴다), "quiet"(해설·혼자 풀기로 갈 때. 알리지 않고, 빈 칸이 있으면 모으지 않는다) */
function setCodeTab(tab, how) {
  const gather = tab === "direct" && S.session && codeEmpty() && S.session.blocks.length > 0;
  const gaps = gather ? emptyBlocks().length > 0 : false;
  if (gaps && how !== "quiet" && !(how === "tab" && S.note.blocks && S.note.blocks.gap)) return warnGaps();
  S.codeTab = tab;
  S.gathering = gather && !gaps ? gatherBlocks() : null; // 서버가 모은다(비동기): 제출·예시 실행은 이것을 기다린다
  if (tab === "direct" && S.note.blocks && S.note.blocks.gap) S.note.blocks = null;
  return false;
}

/** 코드 전체 칸이 비었을 때 블록을 모아 넣는다(서버가 모은다). */
async function gatherBlocks() {
  const pid = S.pid, parts = await composedParts();
  if (!parts || !parts.length || S.pid !== pid || !codeEmpty()) return;
  $("code").value = parts.map(([, text]) => text).join("\n\n") + "\n"; codeChanged(); S.codeNote = "블록 칸의 코드를 모아 왔어요"; say(S.codeNote); warnBraces(parts); render();
}

/** 모아서 실행: 블록을 '코드 전체'로 모아 예시를 실행한다. 코드 전체에 적은 것이 있으면 바꿀지 먼저 묻는다. */
async function composeRun() {
  if (warnGaps()) return;
  if (!codeEmpty()) { S.pullThenRun = true; return askCode("pull"); }
  await pullBlocks();
  S.codeTab = "direct";
  await judgeCode(true);
}

async function pullBlocks() {
  S.codeAsk = null;
  const parts = await composedParts();
  if (!parts) return;
  $("code").value = parts.map(([, text]) => text).join("\n\n") + "\n";
  codeChanged();
  S.codeNote = "블록 칸의 코드를 모아 왔어요";
  say(S.codeNote);
  warnBraces(parts);
  render();
  $("pull-blocks").focus();
}

function renderCodePane() {
  const tutor = tutorWay(S.mode) && !S.choosing && connected();
  $("code-tabs").hidden = !tutor; // 블록으로 쓰기는 튜터 방식에서만
  if (!tutor && S.codeTab !== "direct") setCodeTab("direct", "quiet");
  for (const tab of document.querySelectorAll("#code-tabs [role=tab]")) selectTab(tab, tab.dataset.tab === S.codeTab);
  $("tab-direct").textContent = tutor && !codeEmpty() ? "코드 전체 · 적어 둔 코드 있음" : "코드 전체"; // 코드가 사라진 것처럼 보이지 않게
  $("kept-note").hidden = !(tutor && S.keptNote && S.codeTab === "blocks");
  const direct = S.codeTab === "direct";
  $("panel-direct").hidden = !direct;
  $("panel-blocks").hidden = direct;
  $("compose-run").hidden = !tutor || !S.session.blocks.length || !S.session[S.talk].length; // 시작 전에는 블록 칸이 없다
  $("pull-blocks").hidden = !direct || !S.session.blocks.length || !tutor;
  $("code-note").textContent = direct ? S.codeNote : "제출하면 ‘코드 전체’ 칸의 코드를 채점해요";
  $("run").hidden = !(S.problem.cases && S.problem.cases.example);
  const away = S.busy && S.busy.where === "result" && S.busy.pid !== S.pid; // 다른 문제에서 실행·채점하는 중이면 실행·제출이 잠긴다
  const why = noTool() ? `이 기기에 ${LANG[S.problem.language] || S.problem.language} 도구가 없어 실행과 제출을 할 수 없어요.` : "";
  $("tool-note").textContent = why || (away ? "다른 문제에서 실행·채점하는 중이에요. 끝나면 이 문제도 실행하고 제출할 수 있어요." : "");
  $("run").title = $("submit").title = $("run-own-go").title = why;
  $("run-input").placeholder = (S.problem.examples[0] || { input: "" }).input; // 그 문제 첫 예시의 입력
  $("code").placeholder = program() ? "여기에 전체 코드를 써요. 표준 입력을 읽고 답을 출력해요." : "여기에 전체 코드를 써요. 풀이는 solution 함수에 담아요.";
  $("tool-note").hidden = !why && !away;
  $("starter-note").hidden = S.problem.sample || program() || !!S.problem.starter || !direct; // 등록한 함수 문제인데 케이스에서 형을 정하지 못했다
  const line = S.debug && !S.debug.passed ? S.debug.line : null;
  $("line-note").hidden = !line;
  if (line) $("line-note").innerHTML = `<span>튜터가 짚은 줄: ${line}번째 줄</span><button type="button" class="btn small" id="goto-line">짚은 줄로 가기</button>`;
}

/** 편집기에 표시할 줄: 틀린 곳 같이 찾기에서 튜터가 짚은 줄, 없으면 마지막 결과의 오류 줄(컴파일 오류 줄, 처음 오류가 난 케이스의 줄). 코드를 고치면 사라진다. */
function hitLine() {
  if (S.debug && !S.debug.passed && S.debug.line) return S.debug.line;
  const r = S.result;
  return r && !r.alert && !r.stale ? r.compile_line || r.line || ((r.cases || []).find((c) => c.line) || {}).line || null : null;
}

/* 줄 번호와 짚은 줄 표시. 글상자는 줄바꿈을 하지 않으므로(wrap=off) 줄 번호가 어긋나지 않는다. */
let gutterKey = "", shownHit = null;
function syncGutter() {
  const ta = $("code"), mark = $("line-mark");
  const hit = hitLine();
  const count = ta.value.split("\n").length;
  if (gutterKey !== `${count}:${hit}`) {
    gutterKey = `${count}:${hit}`;
    $("gutter").innerHTML = Array.from({ length: count }, (_, i) => `<span${i + 1 === hit ? ' class="hit"' : ""}>${i + 1}</span>`).join("");
  }
  const height = parseFloat(getComputedStyle(ta).lineHeight) || 22;
  if (hit !== shownHit && ta.clientHeight) { // 새로 짚은 줄이 편집기 밖이면 그 줄이 보이게 스크롤한다(한 번만. 그 뒤의 스크롤은 사용자 것)
    shownHit = hit;
    const top = 10 + (hit - 1) * height;
    if (hit && (top < ta.scrollTop || top + height > ta.scrollTop + ta.clientHeight)) ta.scrollTop = Math.max(0, top - ta.clientHeight / 3);
  }
  $("gutter").scrollTop = ta.scrollTop;
  mark.hidden = !hit || hit > count;
  mark.style.top = `${10 + (hit - 1) * height - ta.scrollTop}px`;
}

function gotoLine() {
  const ta = $("code"), lines = ta.value.split("\n"), n = Math.min(S.debug.line, lines.length);
  const start = lines.slice(0, n - 1).reduce((sum, row) => sum + row.length + 1, 0);
  ta.focus();
  ta.setSelectionRange(start, start + lines[n - 1].length);
  ta.scrollTop = Math.max(0, (n - 4) * (parseFloat(getComputedStyle(ta).lineHeight) || 22));
  syncGutter();
}

function codeChanged() {
  syncGutter();
  S.codeNote = "";
  if (S.result && !S.result.alert && !S.result.stale) { S.result.stale = true; render(); }
  saveCodeSoon();
}

/* 저장: 적다가 잠깐 멈추면 저장한다(코드 전체 → 엔진 문항, 블록 칸 → 화면 서버 파일). */
let codeTimer = null, blocksTimer = null;
function saveCodeSoon() { clearTimeout(codeTimer); codeTimer = setTimeout(saveCode, 1200); }
function saveBlocksSoon() { clearTimeout(blocksTimer); blocksTimer = setTimeout(saveBlocks, 1200); }
async function saveCode() {
  clearTimeout(codeTimer); codeTimer = null;
  if (!S.pid || !S.problem) return;
  $("code")._seen = $("code").value;
  const r = await api("/api/code", { id: S.pid, code: $("code").value, language: S.problem.language }); // 어느 언어의 코드인지(언어를 바꾸는 사이의 옛 코드는 서버가 받지 않는다)
  if (r.ok && !r.data.stale && S.codeTab === "direct" && !S.codeNote) $("code-note").textContent = "저장했어요";
}
function saveBlocks() {
  clearTimeout(blocksTimer); blocksTimer = null;
  if (S.pid && S.problem) api("/api/blocks", { id: S.pid, blocks: S.blockCode, language: S.problem.language });
}
function flushSaves() {
  if (!S.problem) return;
  harvest();
  if (codeTimer || $("code").value !== $("code")._seen) saveCode();
  if (blocksTimer) saveBlocks();
}

/* ── 체크포인트·되돌리기·초기화: 코드 칸만 다룬다(대화와 블록 진행은 그대로. 그것은 '이 문제 처음부터') ── */
function codeError(error) {
  $("code-error").textContent = errorNote(error).text;
  $("code-error").hidden = false;
}

async function saveCheckpoint() {
  harvest();
  const pid = S.pid;
  const r = await work("체크포인트를 남기는 중…", "code", () => api("/api/checkpoint", { id: pid, code: $("code").value, blocks: S.blockCode }));
  if (!r || S.pid !== pid) return;
  if (!r.ok) return codeError(r.error);
  S.problem.checkpoint_at = r.data.at;
  render();
  say("체크포인트를 남겼어요.");
}

function askCode(kind) {
  S.codeAsk = kind;
  S.pullNudge = false;
  render();
  $("code-no").focus();
}

async function restoreCheckpoint() {
  const pid = S.pid;
  S.codeAsk = null;
  clearTimeout(codeTimer); clearTimeout(blocksTimer); codeTimer = blocksTimer = null;
  const r = await work("체크포인트로 되돌리는 중…", "code", () => api("/api/checkpoint/restore", { id: pid, mode: S.talk }));
  if (!r || S.pid !== pid) return;
  if (!r.ok) return codeError(r.error);
  $("code").value = $("code")._seen = r.data.problem.code || r.data.problem.starter || "";
  S.blockCode = r.data.blocks || {};
  if (S.result && !S.result.alert) S.result.stale = true;
  applyState(r.data);
  say("체크포인트로 되돌렸어요.");
  $("cp-restore").focus();
}

/** 초기화: 지금 보는 칸만 비운다. 코드 전체는 시작 코드로, 블록 탭은 블록 칸을 비운다. 자동 저장으로 저장된다. */
function clearCode() {
  S.codeAsk = null;
  if (S.codeTab === "direct") {
    $("code").value = S.problem.starter || "";
    codeChanged();
  } else {
    harvest();
    S.blockCode = {};
    saveBlocksSoon();
  }
  render();
  say(S.codeTab === "direct" && S.problem.starter ? "코드 칸을 시작 코드로 되돌렸어요." : "코드 칸을 비웠어요.");
  $("code-clear").focus();
}

/* ── 채점 결과 ── */
const jsonText = (x) => (Array.isArray(x) ? `[${x.map(jsonText).join(", ")}]` : JSON.stringify(x)); // 배열은 쉼표 뒤에 한 칸
function callText(raw) {
  try { const args = JSON.parse(raw); return Array.isArray(args) ? `solution(${args.map(jsonText).join(", ")})` : raw; } catch (e) { return raw; }
}

const MAX_OWN = 20000; // 직접 입력 글자 수(서버 MAX_INPUT과 같다)
const took = (ms) => (ms >= 1000 ? `${(ms / 1000).toFixed(1)}초` : `${ms}ms`);
// Python에서 아무것도 돌려주지 않으면 None, float('inf')·nan은 inf·-inf·nan(채점기의 JSON은 Infinity·NaN이다. 문자열 안은 그대로)
const shownValue = (v) => (S.problem.language !== "python" ? v : v === "null" ? "None"
  : String(v).replace(/"(?:\\.|[^"\\])*"|-?Infinity|NaN/g, (m) => ({ Infinity: "inf", "-Infinity": "-inf", NaN: "nan" }[m] || m)));
const errText = (c) => `${c.error}${c.line ? ` (${c.line}번째 줄)` : ""}`; // 오류 한 줄 + 채점기가 알려 준 내 코드의 줄
const errHint = (c) => (c.hint ? `<span class="err-hint">${inline(c.hint)}</span>` : ""); // 가져오기 문장(`import heapq`)은 코드로

/** 돌리지 않은 테스트 수를 수치 옆에(계산은 그대로): " · 16개는 돌리지 않음". eff: 효율성 테스트를 센다. */
const unrun = (r, eff) => { const n = r.cases.filter((c) => c.status === "skipped" && (c.kind === "efficiency") === eff).length; return n ? ` · ${n}개는 돌리지 않음` : ""; };

/** 정확성 테스트(공개 예시 + 숨은 테스트)와 효율성 테스트를 나눠 테스트마다 통과 여부와 걸린 시간을 보여 준다.
    숨은 테스트는 통과 여부만 보인다(서버가 입력·기대값을 싣지 않는다). 실행 오류일 때만 예외 이름과 줄 번호, 한 줄 풀이를 칩 아래에 적는다. */
function testsHtml(r) {
  const chip = (c, label) => {
    const cls = c.status === "passed" ? "pass" : c.status === "skipped" ? "skip" : "fail";
    const time = c.status === "skipped" ? "" : `<span class="ms">${took(c.ms || 0)}${c.status === "timeout" ? " 넘음" : ""}</span>`; // 시간 초과는 제한을 넘은 것
    return `<span class="test ${cls}">${label}${c.kind === "example" ? " <em>예시</em>" : ""} <b>${esc(CASE_STATE[c.status] || c.status)}</b> ${time}</span>`;
  };
  const acc = r.cases.filter((c) => c.kind !== "efficiency"), eff = r.cases.filter((c) => c.kind === "efficiency");
  const pre = (label, text, bad) => `<div><span class="io-label">${label}</span><pre class="code${bad ? " bad" : ""}"><code>${esc(text)}</code></pre></div>`;
  const io = (c, ok) => `<div class="io-case">${pre("입력", c.input || "(입력 없음)")}<div class="io-pair">${pre("기대 출력", c.expected)}${pre("내 출력", c.got || "(아무것도 출력하지 않았어요)", !ok)}</div>
    ${c.error ? `<p class="hint bad">${esc(errText(c))}${errHint(c)}</p>` : ""}</div>`; // 표준 입출력: 기대 출력과 내 출력을 나란히 두고 줄마다 견준다
  const detail = (c, n) => {
    const ok = c.status === "passed";
    const head = `<summary class="case-head"><span>테스트 ${n} · 예시</span><span class="state">${esc(CASE_STATE[c.status] || c.status)}${c.status === "skipped" ? "" : ` <span class="ms">${took(c.ms || 0)}</span>`}</span></summary>`;
    if (program()) return `<details class="case ${ok ? "pass" : "fail"}"${ok ? "" : " open"}>${head}${io(c, ok)}</details>`;
    return `<details class="case ${ok ? "pass" : "fail"}"${ok ? "" : " open"}>${head}
      <dl><dt>넣은 값</dt><dd>${esc(callText(c.input))}</dd><dt>기대한 결과</dt><dd>${esc(c.expected)}</dd>
        <dt>내 코드의 결과</dt><dd${ok ? "" : ' class="bad"'}>${esc(c.got ? shownValue(c.got) : "(아무것도 돌려주지 않았어요)")}</dd>${c.error ? `<dt>오류</dt><dd class="bad">${esc(errText(c))}${errHint(c)}</dd>` : ""}</dl></details>`;
  };
  const score = r.score || { accuracy: [acc.filter((c) => c.status === "passed").length, acc.length], efficiency: [0, 0] };
  const hiddenErrors = (list, label) => { // 숨은 테스트의 오류 → 그 오류가 난 테스트 번호들(같은 오류는 한 줄로)
    const errors = new Map();
    list.forEach((c, i) => { if (c.kind !== "example" && c.error) { const key = errText(c); if (!errors.has(key)) errors.set(key, { c, ns: [] }); errors.get(key).ns.push(i + 1); } });
    return [...errors].map(([line, { c, ns }]) => `<p class="hint bad">${label} ${ns.join(", ")} · ${esc(line)}${errHint(c)}</p>`).join("");
  };
  let html = `<h4 class="tests-title">${r.run ? "공개 예시" : "정확성 테스트"} <span>${score.accuracy[0]} / ${score.accuracy[1]}${unrun(r, false)}</span></h4>
    ${acc.map((c, i) => [c, i + 1]).filter(([c]) => c.kind === "example").map(([c, n]) => detail(c, n)).join("")}
    <div class="tests">${acc.map((c, i) => (c.kind === "example" ? "" : chip(c, `테스트 ${i + 1}`))).join("")}</div>
    ${hiddenErrors(acc, "테스트")}`;
  if (eff.length) {
    html += `<h4 class="tests-title">효율성 테스트 <span>${score.efficiency[0]} / ${score.efficiency[1]}${unrun(r, true)}</span></h4>
      <p class="hint">아주 큰 입력에서 제한 시간 안에 끝나는지 봐요. 입력은 보여 주지 않아요.</p>
      <div class="tests">${eff.map((c, i) => chip(c, `효율성 ${i + 1}`)).join("")}</div>${hiddenErrors(eff, "효율성")}`;
  }
  return html;
}

/** 채점기가 코드를 돌리지 못한 까닭(함수 없음, 컴파일 오류, 도구 없음 …). */
function judgeFail(r) {
  const p = S.problem;
  let [title, tip] = (program() && JUDGE_PROGRAM[r.status]) || JUDGE_STATE[r.status] || ["채점하지 못했어요", ""];
  if (r.status === "compile_error" && ["python", "javascript"].includes(p.language)) title = "문법 오류가 났어요"; // 컴파일하지 않는 언어
  const tool = r.status === "toolchain_missing" ? `필요한 도구: ${TOOL[p.language] || p.language}. 설치한 뒤 다시 제출하거나, 위에서 다른 언어를 골라 주세요.` : tip;
  const other = ["entry_missing", "undecided"].includes(r.status) && r.looks && r.looks !== p.language ? r.looks : null;
  return `<p class="verdict fail"><span class="badge">${ico("i-x")}</span>${esc(title)}</p>${tool ? `<p class="hint">${esc(tool)}</p>` : ""}
    ${other ? `<p class="hint bad">고른 언어는 ${esc(LANG[p.language] || p.language)}인데 코드는 ${esc(LANG[other])}처럼 보여요. 언어를 바꾸거나 코드를 고쳐 주세요.</p>` : ""}
    ${r.compile ? `<pre class="code"><code>${esc(r.compile)}</code></pre>` : ""}`;
}

/** 직접 넣은 값으로 한 번 실행한 결과: 넣은 값, 돌려준 값, 걸린 시간, 오류 한 줄. 맞았는지는 판정하지 않는다.
    기본 문제는 정답 풀이의 결과를 함께 보이고 돌려준 값과 같은지 알린다(제출이 아니다). */
function ownHtml(r) {
  if (r.status !== "ran" && !CASE_STATE[r.status]) return judgeFail(r); // 돌리지 못했다
  if (program()) { // 표준 입출력: 넣은 글과 출력 전체(오류로 멈췄으면 그때까지 쓴 것)
    const box = (text) => `<pre class="code"><code>${esc(text)}</code></pre>`;
    return `<h4 class="tests-title">직접 넣은 입력으로 실행 <span>${r.status === "ran" ? took(r.ms || 0) : esc(CASE_STATE[r.status])}</span></h4>
      <dl class="own-run"><dt>입력</dt><dd>${box(r.input || "(입력 없음)")}</dd><dt>출력</dt><dd>${box(r.got || "(아무것도 출력하지 않았어요)")}</dd>
        ${r.error ? `<dt>오류</dt><dd class="bad">${esc(errText(r))}${errHint(r)}</dd>` : ""}</dl>`;
  }
  const value = (v) => `<pre class="code"><code>${esc(v ? shownValue(v) : "(아무것도 돌려주지 않았어요)")}</code></pre>`;
  return `<h4 class="tests-title">직접 넣은 값으로 실행 <span>${r.status === "ran" ? took(r.ms || 0) : esc(CASE_STATE[r.status])}</span></h4>
    <dl class="own-run"><dt>넣은 값</dt><dd>${esc(callText(r.input))}</dd>
      ${r.status === "ran" ? `<dt>돌려준 값</dt><dd>${value(r.got)}</dd>` : ""}
      ${r.reference !== undefined ? `<dt>정답 풀이의 결과</dt><dd>${value(r.reference)}${r.same === undefined ? "" : `<span class="same ${r.same ? "pass" : "fail"}">${r.same ? "같아요" : "달라요"}</span>`}</dd>` : ""}
      ${r.stdout ? `<dt>찍은 것</dt><dd><pre class="code"><code>${esc(r.stdout)}</code></pre></dd>` : ""}
      ${r.error ? `<dt>오류</dt><dd class="bad">${esc(errText(r))}${errHint(r)}</dd>` : ""}</dl>
    ${r.reference_note ? `<p class="hint">${esc(r.reference_note)}</p>` : ""}`;
}

/** 틀린 까닭에 맞는 안내 한 줄(위에서부터 처음 맞는 것). */
function failGuide(r, slowOnly) {
  const stuck = (c) => c.status === "timeout" || c.status === "skipped";
  const examplesOk = r.cases.every((c) => c.kind !== "example" || c.status === "passed"), hidden = r.cases.filter((c) => c.kind === "accuracy");
  if (r.cases.length && r.cases.every(stuck)) return "코드가 끝나지 않았어요. 반복이 끝나는 조건을 확인해 보세요.";
  if (r.run) return "";
  if (examplesOk && hidden.some(stuck)) return "숨은 테스트에서 시간 초과가 났어요. 어떤 입력에서 반복이 끝나지 않거나 아주 오래 도는지 확인해 보세요.";
  if (examplesOk && hidden.some((c) => c.status !== "passed")) return "예시는 통과했지만 숨은 테스트에서 틀렸어요. 가장 작은 입력, 같은 값이 여러 개인 입력, 가장 큰 입력을 직접 만들어 확인해 보세요.";
  if (slowOnly) return "답은 모두 맞아요. 입력이 아주 클 때 시간이 모자라요. 제한사항의 입력 크기를 보고, 같은 것을 되풀이해 세거나 찾는 곳이 없는지 살펴보세요.";
  return "";
}

function renderResult() {
  const box = $("result"), r = S.result, judging = S.busy && S.busy.where === "result", mine = judging && S.busy.pid === S.pid;
  box.hidden = !r && !mine;
  if (mine) return void (box.innerHTML = `<div class="note">${waitLine("result").replace(" · 보통 5~25초 걸려요", "")}</div>`);
  if (!r) return void (box.innerHTML = "");
  if (r.alert) return void (box.innerHTML = noteHtml(r.alert));
  const notice = r.notice ? `<p class="hint">${esc(r.notice)}</p>` : ""; // 채점 실행 제한을 걸지 못했다(Windows 작업 객체)
  if (r.own) return void (box.innerHTML = ownHtml(r) + notice + (r.stale ? '<div class="note warn" role="status">코드를 고쳤어요. 다시 실행하면 새로 돌려요.</div>' : ""));
  const total = r.cases.length, p = S.problem;
  const finding = S.debug && S.debug.open;
  const score = r.score || { accuracy: [0, 0], efficiency: [0, 0] };
  const counts = `정확성 ${score.accuracy[0]}/${score.accuracy[1]}${unrun(r, false)}${score.efficiency[1] ? ` · 효율성 ${score.efficiency[0]}/${score.efficiency[1]}${unrun(r, true)}` : ""}`;
  const slowOnly = !r.ok && !r.run && total && score.accuracy[0] === score.accuracy[1] && score.efficiency[1] > 0; // 답은 맞고 큰 입력에서만 걸렸다
  const hidden = p.cases.accuracy + p.cases.efficiency > 0; // 숨은 테스트가 있는가(등록한 문제는 '숨김'을 켠 케이스)
  const skipped = r.cases.filter((c) => c.status === "skipped").length, near = r.cases.find((c) => c.near);
  let html = "";
  if (r.run) html += r.ok ? `<p class="verdict pass"><span class="badge">${ico("i-check")}</span>예시 통과 <small>공개 예시 ${total}개를 맞혔어요. ${hidden ? "제출하면 숨은 테스트까지 채점해요" : "제출하면 기록으로 남아요"}</small></p>`
    : total ? `<p class="verdict ${r.many ? "unsure" : "fail"}"><span class="badge">${ico(r.many ? "i-warn" : "i-x")}</span>${r.many ? MANY_HEAD : "예시에서 틀려요"} <small>공개 예시 ${total}개 중 ${score.accuracy[0]}개 통과</small></p>` : "";
  else if (r.ok) html += `<p class="verdict pass"><span class="badge">${ico("i-check")}</span>통과 <small>${counts}${hidden ? "" : ` · 공개 예시 ${total}개로만 채점했어요`}</small></p>`;
  else if (total) html += `<p class="verdict ${r.many ? "unsure" : "fail"}"><span class="badge">${ico(r.many ? "i-warn" : "i-x")}</span>${r.many ? MANY_HEAD : slowOnly ? "답은 맞지만 느려요" : "아직 틀려요"} <small>${counts}${hidden ? "" : ` · 공개 예시 ${total}개로만 채점했어요`}</small></p>`;
  if (!total) html += judgeFail(r);
  const ai = connected(), learn = p.study.has_guide && (r.ok || p.passed > 0);
  const tutorSide = ai && tutorWay(S.mode), talked = tutorSide && S.session[S.mode].length > 0; // 튜터 방식: 도움도 그 안에서(방식을 말없이 바꾸지 않는다)
  let acts = "";
  if (!r.run && r.ok) { // 통과: 다음 문제(그 주제의 다음 단계). 곁에 덜 눈에 띄게 피드백, 실전 신호
    const nx = S.nextUp;
    acts = `<a id="result-next" class="btn" href="${nx ? `#/p/${esc(nx.id)}` : "#/list"}"${nx ? ` title="${esc(nx.title)}"` : ""}>${nx ? "다음 문제" : "문제 목록으로"}</a>${nx ? `<span class="hint next-title">${esc(nx.title)}</span>` : ""}
      ${ai ? '<button type="button" id="to-feedback" class="btn quiet" data-model>피드백 받기</button>' : ""}${learn ? `<button type="button" id="result-learn" class="btn quiet"${tutorWay(S.mode) ? ' title="푸는 방식이 혼자 풀기로 바뀌어요"' : ""}>실전 신호 보기${tutorWay(S.mode) ? " · 혼자 풀기로 바뀌어요" : ""}</button>` : ""}`;
  } else if (!r.ok && total) {
    const finds = ai && !slowOnly && (!r.run || tutorSide); // 튜터 방식이면 예시 실행에서 틀렸을 때도 틀린 곳 같이 찾기가 먼저다
    if (finds) acts += '<button type="button" id="debug-start" class="btn" data-model>틀린 곳 같이 찾기</button>';
    if (talked) acts += `<button type="button" id="result-tutor-hint" class="btn quiet" data-model title="튜터가 지금 블록의 다음 힌트를 말해요">${ico("i-bulb")}이 블록 힌트 받기</button>`;
    else if (S.solo && S.solo.total) acts += `<button type="button" id="result-hint" class="btn${finds ? " quiet" : ""}" title="${tutorWay(S.mode) ? "푸는 방식이 혼자 풀기로 바뀌고, 풀이를 처음부터 하나씩 짚는 힌트를 열어요" : "풀이를 처음부터 하나씩 짚는 힌트예요"}">${ico("i-bulb")}풀이 힌트 보기${tutorWay(S.mode) ? " · 혼자 풀기로 바뀌어요" : ""}</button>`;
    if (!r.run && ai) acts += '<button type="button" id="to-feedback" class="btn quiet" data-model>피드백 받기</button>';
  }
  if (acts) html += `<div class="result-actions">${acts}</div>`;
  const right = !r.ok && ((S.debug && S.debug.open) || (S.mode === "solo" && S.soloOpen === "hint"));
  if (right) html += '<p class="flow-note" role="status">오른쪽에서 이어져요 →</p>'; // 도움은 오른쪽 칸에 뜬다
  const guide = !r.ok && total ? failGuide(r, slowOnly) : "";
  if (guide) html += `<div class="note warn" role="status">${guide}</div>`;
  if (r.stale) html += `<div class="note warn" role="status">코드를 고쳤어요. 다시 ${r.run ? "실행" : "제출"}하면 새로 채점해요.</div>`;
  if (skipped) html += `<p class="hint">시간 초과가 세 번 이어져 남은 테스트 ${skipped}개는 돌리지 않았어요.</p>`;
  if (near) html += `<p class="hint">제한 시간에 가까워요(${(near.ms / 1000).toFixed(1)}초 / ${Number(near.limit).toFixed(1)}초). 기기 상태에 따라 결과가 달라질 수 있어요.</p>`;
  // 테스트 목록은 틀렸을 때와 예시 실행 때 펼쳐 둔다. 다 맞았거나 틀린 곳을 찾는 중이면 접는다. 사용자가 펼치면 그대로 둔다
  if (total) html += `<details class="case-fold"${(S.casesOpen ?? (!finding && !r.ok)) ? " open" : ""}><summary>테스트별 결과</summary>${testsHtml(r)}</details>`;
  if (r.repeat) html += '<p class="hint">직전 제출과 같은 코드라 제출 기록은 그대로예요.</p>';
  if (r.unsaved) html += '<p class="hint">틀린 곳을 찾으며 다시 채점한 결과라 제출 기록에는 남지 않았어요. 남기려면 제출해 주세요.</p>';
  box.innerHTML = html + notice;
}

async function submitCode() {
  await judgeCode(false);
}

/** 예시 실행(run: 공개 예시만, 제출로 남지 않는다), 직접 넣은 값으로 실행(input: 한 번, 판정 없음)과 제출(모든 테스트). */
async function judgeCode(run, input) {
  const pid = S.pid;
  if (S.codeAsk === "pull") { // 모을지 묻는 중이다: 답하기 전에는 옛 코드를 말없이 채점하지 않고, 같은 자리에서 다시 묻는다
    S.pullNudge = true;
    render();
    return void $("code-no").focus();
  }
  if (codeEmpty()) {
    if (setCodeTab("direct")) return; // 빈 블록이 있어 모으지 않고 알렸다
    await S.gathering;
    if (S.pid !== pid) return;
    const pulled = !codeEmpty();
    S.result = { alert: { type: "warn", text: pulled ? `블록 칸의 코드를 ‘코드 전체’에 모아 왔어요. ${program() ? "프로그램으로" : "solution 함수로"} 완성한 뒤 다시 제출해 주세요.`
      : $("code").value.trim() ? "아직 시작 코드 그대로예요. 풀이를 쓴 뒤 다시 눌러 주세요." // 칸에 시작 코드가 보이는데 '코드를 써야'라고 하면 헷갈린다
      : `${tutorWay(S.mode) && connected() ? "‘코드 전체’ 칸" : "코드 칸"}에 코드를 써야 채점할 수 있어요.` } }; // 탭이 보일 때만 탭 이름을 쓴다
    render();
    return $("code").focus();
  }
  const code = $("code").value;
  const own = input !== undefined;
  if (own && input.length > MAX_OWN) { S.result = { alert: { type: "error", text: "직접 입력은 20,000자까지 넣을 수 있어요." } }; return render(); } // 서버의 본문 상한(1MB)보다 먼저 알린다
  const r = await work(own ? "직접 넣은 값으로 실행하는 중…" : run ? "예시를 실행하는 중…" : "채점하는 중…", "result", () => api(run ? "/api/run" : "/api/submit", { id: pid, code, ...(own ? { input } : {}) }));
  if (!r || S.pid !== pid) return;
  $("code")._seen = code;
  S.result = r.ok ? { ...r.data, run, own, looks: looksLike(code) } : { alert: errorNote(r.error) };
  S.casesOpen = null;
  say(!r.ok ? "" : own ? "직접 넣은 값으로 실행했어요." : run ? (r.data.ok ? "예시를 모두 맞혔어요." : r.data.many ? `${MANY_HEAD}.` : "예시에서 틀려요.") : r.data.ok ? "채점 결과: 통과" : `채점 결과: ${r.data.many ? MANY_HEAD : "아직 틀려요"}`);
  if (run) return render();
  await loadState();
  if (r.ok && r.data.ok) { await loadNextUp(); if (S.problem.study.has_guide) await loadSolution(false); } // 통과하면 결과 바로 아래 '다음 문제'를 채우고 해설을 연다
}

/** 다음 문제(nextOf)를 학습 보고서에서 받아 둔다. 결과·해설 칸이 이것을 쓴다. */
async function loadNextUp() {
  const pid = S.pid, rep = await api("/api/report");
  if (S.pid !== pid) return;
  S.nextUp = rep.ok ? nextOf(rep.data.next, pid) : null;
  render();
}

/* ── 오른쪽 칸: 어떻게 풀까요(혼자 풀기 · 튜터와 차례로 · 튜터의 질문으로) ── */
function selectTab(tab, on) {
  tab.setAttribute("aria-selected", on ? "true" : "false");
  tab.tabIndex = on ? 0 : -1;
}

/** 방식을 바꾼다. remember: 사용자가 고른 것(이 문제에 기억한다). */
function setMode(mode, remember) {
  S.choosing = false;
  if (remember) saveWay(S.pid, mode);
  if (mode === S.mode && !(S.debug && S.debug.open)) return render();
  S.mode = mode;
  S.quote = null;
  if (S.debug) S.debug.open = false;
  const tutor = tutorWay(mode);
  if (tutor) S.talk = mode;
  if (tutor && !codeEmpty() && !S.keptSeen) S.keptNote = S.keptSeen = true; // 적어 둔 코드가 있는 채 튜터를 시작: 한 번 알린다
  setCodeTab(tutor ? "blocks" : "direct", "quiet"); // 혼자 풀기·해설은 코드 전체, 튜터 둘은 블록이 먼저
  render();
  return loadState();
}

/** 고르는 칸: 카드 셋. 연결이 없으면 튜터 둘은 흐리게 두고 까닭과 연결하는 길을 말한다. */
function renderWay() {
  const ai = connected();
  $("way-box").innerHTML = `<div class="ways" role="group" aria-label="푸는 방식">${["solo", "guide", "chair"].map((k) => `<button type="button" class="way-card" data-way="${k}"${k !== "solo" && !ai ? " disabled" : ""} aria-describedby="way-${k}">
      <strong>${WAYS[k][0]}${S.mode === k ? '<em class="tag">지금 방식</em>' : ""}</strong><span id="way-${k}">${WAYS[k][1]}</span></button>`).join("")}</div>
    ${ai ? '<p class="hint">고른 방식은 이 문제에 기억해요. 위의 ‘방식 바꾸기’로 언제든 바꿔요.</p>' : '<div class="note"><span>튜터 둘은 AI를 연결하면 쓸 수 있어요.</span><button type="button" class="btn small" id="note-conn">연결하기</button></div>'}`;
}

function renderTutor() {
  const s = S.session, mode = S.mode, finding = !!(S.debug && S.debug.open), choosing = !mode || S.choosing;
  const solo = mode === "solo" && !choosing, railed = solo && !S.soloOpen && !finding;
  $("panes").classList.toggle("railed", railed); // 혼자 풀기는 오른쪽 칸을 접어 '힌트'·'해설' 두 단추만 둔다
  $("way-title").textContent = finding ? "튜터" : choosing ? "어떻게 풀까요?" : mode === "explain" ? START.explain[0] : WAYS[mode][0];
  $("way-change").hidden = finding || (choosing && !mode);
  $("way-change").textContent = choosing ? "그대로 두기" : "방식 바꾸기";
  $("solo-tabs").hidden = $("solo-fold").hidden = !solo || !S.soloOpen || finding;
  for (const tab of document.querySelectorAll("#solo-tabs [role=tab]")) selectTab(tab, tab.dataset.solo === S.soloOpen);
  $("way-box").hidden = finding || !choosing;
  if (choosing) renderWay();
  $("rail").hidden = !railed;
  if (railed && S.solo) $("rail-hint").lastChild.textContent = S.solo.total ? `힌트 ${S.solo.seen}/${S.solo.total}` : "힌트";
  $("solo-box").hidden = finding || !solo || !S.soloOpen;
  if (solo && S.soloOpen) renderSolo();
  const talking = !choosing && (tutorWay(mode) || mode === "explain");
  const chat = tutorWay(mode) ? s[mode] : [];
  const started = mode === "explain" ? !!s.explain : chat.length > 0;
  $("start-box").hidden = finding || !talking || started;
  $("explain-box").hidden = finding || !talking || mode !== "explain" || !started;
  $("chat-log").hidden = finding || !talking || mode === "explain" || !started;
  $("composer").hidden = finding || !talking || mode === "explain" || !started || !!S.quote;
  $("fq-composer").hidden = finding || !talking || mode === "explain" || !started || !S.quote;
  if (!talking) return;

  if (!started) {
    const [title, text, button] = START[mode];
    const preparing = !connected() ? "" : S.problem.preparing ? `<div class="note" role="status">${DOTS}<span>튜터가 이 문제의 풀이 순서를 준비하고 있어요. <span class="secs" data-since="${S.prepAt}">${since(S.prepAt)}초</span> · <span data-late="30초쯤 걸려요">${late(since(S.prepAt), "30초쯤 걸려요")}</span></span></div>`
      : S.problem.prepare_failed && !S.note.start ? noteHtml(PREP_FAILED) : ""; // 뒤에서 준비하다 실패했다: 다시 준비(미리 만들기를 다시 탄다)
    $("start-box").innerHTML = `<h3>${title}</h3><p>${text}</p>
      <button type="button" id="start" class="btn" data-model>${button}</button>
      ${S.busy && S.busy.where === "start" ? `<div class="note">${waitLine("start").replace("보통 5~25초 걸려요", `<span data-late="처음은 30초쯤 걸려요">${late(secs(), "처음은 30초쯤 걸려요")}</span>`)}</div>` : preparing}${noteHtml(S.note.start)}`;
    return;
  }
  if (mode === "explain") {
    $("explain-box").innerHTML = s.explain.sections.map((x, i) => `<section class="section"><h3><span class="no">${i + 1}</span>${esc(x.title)}</h3>${rich(x.body)}</section>`).join("");
    return;
  }

  let n = 0, html = "", aimed = null; // aimed: 앞 튜터 말이 겨눈 블록 번호
  chat.forEach((m, i) => {
    if (m.role !== "service") return void (html += meMsg(m.text));
    n += 1;
    let kind = null, no = "";
    if (Number.isInteger(m.block_index)) { // 그 말이 겨눈 블록(엔진이 준다)의 종류와 순번. 블록이 바뀌는 말 위에만
      const b = s.blocks[m.block_index];
      if (b && m.block_index !== aimed) [kind, no] = [b.kind, ` ${m.block_index + 1}`];
      aimed = m.block_index;
    } else { // block_index가 없는 예전 기록: 새 블록을 알리는 말, 또는 첫 말이면 첫 블록
      const next = NEXT_BLOCK.exec(m.text);
      kind = next ? KIND_BY_LABEL[next[1]] : i === 0 && s.blocks[0] ? s.blocks[0].kind : null;
    }
    const thread = (s.followups.find((t) => t.quote_id === m.id) || { messages: [] }).messages;
    const quoted = S.quote === m.id;
    if (kind) html += `<div class="turn">${kindChip(kind)}<span>블록${no}</span></div>`;
    html += `<div class="msg tutor${quoted ? " is-quoted" : ""}" data-msg="${esc(m.id)}"><span class="who">튜터</span><div class="bubble">${rich(m.text)}</div>
      <div class="msg-tools"><button type="button" class="btn quiet small" data-quote="${esc(m.id)}" aria-label="${n}번째 튜터 말에 꼬리질문"${quoted ? ' aria-pressed="true"' : ""}>꼬리질문</button></div></div>`;
    const waiting = quoted && S.busy && S.busy.where === "thread";
    if (thread.length || waiting) {
      html += `<div class="thread" role="group" aria-label="${n}번째 튜터 말의 꼬리질문"><span class="thread-title">꼬리질문</span>
        ${thread.map((x) => (x.role === "service" ? tutorBubble(x.text) : meMsg(x.text))).join("")}
        ${waiting && S.sending ? meMsg(S.sending.text, true) : ""}${waiting ? pending("thread") : ""}</div>`;
    }
  });
  const last = chat[chat.length - 1], gaps = last && last.role === "service" && /^블[록럭]을 모두 채웠어요/.test(last.text) ? emptyBlocks() : [];
  if (gaps.length) html += `<p class="notice warn" role="status">${esc(gapText(gaps))}</p>`; // 엔진의 고정 안내 아래에 빈 칸을 알린다
  if (S.busy && S.busy.where === "chat") html += (S.sending ? meMsg(S.sending.text, true) : "") + pending("chat");
  else if (allFound()) html += '<p class="notice" role="status">블록을 모두 찾았어요. 블록 칸을 채우고 ‘모아서 실행’을 눌러 보세요.</p>';
  html += noteHtml(S.note.chat);
  const log = $("chat-log"), key = `${mode}:${chat.length}:${s.followups.reduce((sum, t) => sum + t.messages.length, 0)}:${S.busy ? S.busy.where : ""}:${S.quote}:${(S.note.chat || {}).text}`;
  log.innerHTML = html;
  if (log._key !== key) { // 새 말이 오면 그 말이 보이게
    log._key = key;
    const target = S.quote && log.querySelector(`[data-msg="${CSS.escape(S.quote)}"]`);
    if (target) (target.nextElementSibling && target.nextElementSibling.classList.contains("thread") ? target.nextElementSibling : target).scrollIntoView({ block: "nearest" });
    else log.scrollTop = log.scrollHeight;
  }
  if (S.quote) $("fq-quote").textContent = (chat.find((m) => m.id === S.quote) || { text: "" }).text;
}

/* ── 혼자 풀기: 미리 만들어 둔 힌트와 해설(모델 0회) ── */
function solutionHtml(sol, passed) {
  const guide = sol.approach || sol.clues.length || sol.steps.length;
  const r = S.result, shownNext = r && r.ok && !r.run && !r.stale; // 결과 상자에 '다음 문제'가 있으면 여기에는 두지 않는다(같은 곳으로 가는 길은 하나)
  const next = shownNext ? "" : `<div class="solo-next">${S.nextUp ? `<a class="btn" href="#/p/${esc(S.nextUp.id)}">다음 문제: ${esc(S.nextUp.title)}</a>` : ""}</div>`;
  return `${passed ? `<p class="verdict pass"><span class="badge">${ico("i-check")}</span>통과했어요 <small>이 문제에서 가져갈 것</small></p>${next}` : ""}
    <h4>실전 신호</h4><p class="hint">실전에서 문제 글에 이런 표현이 보이면 이렇게 떠올려요.</p>
    <ul class="signals">${sol.signals.map((x) => `<li class="signal">${x.phrase ? `<q>${esc(x.phrase)}</q>` : ""}<span>${esc(x.means)}</span></li>`).join("")}</ul>
    ${sol.pattern || sol.learn ? `<h4>이 문제로 익힌 것 <span class="tag">${esc(sol.pattern)}</span></h4><p>${esc(sol.learn)}</p>` : ""}
    ${sol.pitfalls.length ? `<h4>흔한 실수</h4><ul class="plain-list">${sol.pitfalls.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
    <details class="solution"${passed ? "" : " open"}><summary>풀이 해설과 정답 코드</summary>
      ${sol.verified === false || sol.verified === null ? '<p class="hint">이 풀이는 테스트로 확인하지 못했어요.</p>' : ""}
      ${sol.approach ? `<h4>푸는 방향</h4><p>${esc(sol.approach)}</p>` : ""}
      ${sol.clues.length ? `<h4>문제 글에서 읽어낸 것</h4><ul class="plain-list">${sol.clues.map((x) => `<li>${inline(x)}</li>`).join("")}</ul>` : ""}
      ${sol.steps.length ? `<h4>푸는 순서</h4><ol class="plain-list numbered">${sol.steps.map((x) => `<li>${inline(x)}</li>`).join("")}</ol>` : ""}
      <h4>정답 풀이 <span class="tag">${esc(LANG[sol.language] || sol.language)}</span></h4>${guide ? "" : '<p class="hint">이 문제는 글로 된 해설이 아직 없어요. 정답 코드만 있어요.</p>'}
      <pre class="code"><code>${esc(sol.code.replace(/\s+$/, ""))}</code></pre></details>${passed ? "" : next}`;
}

function renderSolo() {
  const p = S.problem, o = S.solo, ai = connected();
  if (S.soloOpen === "hint") {
    let hints = `<section class="solo-sec" aria-labelledby="solo-hints"><h3 id="solo-hints">${ico("i-bulb")}풀이 힌트${o.total ? ` <span class="muted">${o.seen} / ${o.total}</span>` : ""}</h3>`;
    if (!o.total) hints += `<p class="hint">이 문제에는 미리 만들어 둔 힌트가 없어요. ${ai ? "‘방식 바꾸기’에서 ‘튜터의 질문으로’를 고르면 튜터가 질문으로 도와줘요." : "튜터를 연결하면 질문으로 도와줘요."}</p>`;
    else {
      // 머리: 블록 번호와 종류, 그 블록의 힌트를 모두 본 뒤에는 블록 이름(서버가 그때만 보낸다). '단계'는 난이도에만 쓴다
      hints += `<p class="hint">풀이를 처음부터 차례로 짚어요. 답을 알려 주지 않고 생각할 거리를 하나씩 드려요. 풀이의 블록마다 힌트가 세 개씩 있어요.</p>
        ${o.shown.length ? `<ol class="hints">${o.shown.map((h) => `<li><span class="hint-no">${h.kind ? kindChip(h.kind) : ""}블록 ${h.block}${h.name ? ` · ${esc(h.name)}` : ""} · 힌트 ${h.step}</span><p>${esc(h.hint)}</p></li>`).join("")}</ol>` : ""}
        ${o.seen >= o.total ? '<p class="hint">힌트를 모두 봤어요. 여기까지 보고도 막히면 ‘해설’을 열어 보세요.</p>' : `<button type="button" id="solo-hint" class="btn">${o.shown.length ? "다음 힌트 보기" : "첫 힌트 보기"}</button>`}`;
    }
    $("solo-box").innerHTML = hints + "</section>";
    return;
  }
  let sol = `<section class="solo-sec" aria-labelledby="solo-sol"><h3 id="solo-sol">${ico("i-check")}실전 신호와 해설</h3>`;
  const tutorExplain = ai ? '<button type="button" id="to-explain" class="btn quiet small" data-model>튜터에게 해설 받기</button>' : ""; // 모델이 쓰는 해설(예전 '해설' 탭)
  if (!p.study.has_guide) sol += `<p class="hint">이 문제에는 미리 만든 해설이 없어요. ${ai ? "튜터가 써 줄 수 있어요." : "튜터를 연결하면 해설을 써 줘요."}</p>${tutorExplain}`;
  else if (o.sol) sol += solutionHtml(o.sol, p.passed > 0) + tutorExplain;
  else if (p.study.solution_open) sol += `${p.passed && !p.study.passed_now ? '<p class="hint">다시 푸는 중이에요. 지금 해설을 열면 이번 풀이는 도움을 받은 것으로 남아요.</p>' : ""}<button type="button" id="solo-open" class="btn">해설 보기</button>`; // '처음부터' 뒤에 이미 통과한 문제
  else if (o.ask) sol += `<div class="note warn"><span>통과하기 전에 해설을 보면 학습 보고서에 ‘해설을 먼저 봄’으로 남아요. 힌트를 끝까지 본 뒤에 여는 것을 권해요.</span></div>
    <div class="solo-actions"><button type="button" id="solo-force-yes" class="btn danger small">그래도 해설 보기</button><button type="button" id="solo-force-no" class="btn small">더 풀어 볼게요</button></div>`;
  else sol += `<p class="hint lock-line">${ico("i-lock")}통과하면 이 문제의 실전 신호와 해설이 열려요.</p><button type="button" id="solo-force" class="btn quiet small">포기하고 해설 보기</button>`;
  $("solo-box").innerHTML = sol + `${noteHtml(o.note)}</section>`;
}

async function loadHints(peek) {
  const pid = S.pid, r = await api("/api/hint", { id: pid, peek });
  if (S.pid !== pid || !S.solo) return;
  if (r.ok) Object.assign(S.solo, { shown: r.data.shown, seen: r.data.seen, total: r.data.total, note: null });
  else if (!peek) S.solo.note = errorNote(r.error);
  render();
  if (r.ok && !peek) { say("힌트를 하나 열었어요."); const last = $("solo-box").querySelector(".hints li:last-child"); if (last) last.scrollIntoView({ block: "nearest" }); }
}

async function loadSolution(force) {
  const pid = S.pid, r = await api("/api/solution", { id: pid, force });
  if (S.pid !== pid || !S.solo) return;
  if (r.ok) { S.solo.sol = r.data; S.solo.ask = false; S.problem.study.solution_open = true; }
  else if (r.error.code !== "unknown") S.solo.note = errorNote(r.error); // 잠겨 있으면(409) 그대로 둔다
  render();
  if (r.ok && !S.nextUp) await loadNextUp(); // 해설 칸의 ‘다음 문제’
}

async function changeLanguage(language) {
  const pid = S.pid, code = $("code").value;
  clearTimeout(codeTimer); clearTimeout(blocksTimer); codeTimer = blocksTimer = null;
  S.langWant = null;
  $("code").readOnly = true; // 바꾸는 동안 적은 옛 언어의 코드가 새 언어 칸에 저장되지 않게 잠근다. 다 바꾸면 서버가 준 새 언어의 코드로 채운다
  // 튜터가 뒤에서 이 문제의 계획을 만드는 중이면 그것이 끝날 때까지 기다린다(길면 30초쯤). 그동안 무엇을 하는지 보여 준다
  const r = await work(`언어를 바꾸는 중: ${LANG[language] || language}…`, "lang", () => api("/api/language", { id: pid, language, ...(codeEmpty() ? {} : { code }) })) // 시작 코드뿐이면 저장하지 않는다
    .finally(() => { $("code").readOnly = false; });
  if (!r || S.pid !== pid) return;
  if (!r.ok) { $("code-error").textContent = errorNote(r.error).text; $("code-error").hidden = false; return render(); }
  clearProblem(pid);
  applyState(r.data);
  if (ACCOUNTS) ACCOUNTS.language = language; // 서버가 기억한 마지막 언어(등록 화면의 기본값)
  say(`언어를 바꿨어요: ${LANG[language] || language}`);
}

function wantLanguage(language) {
  const s = S.session;
  harvest();
  const progressed = s.chair.length || s.guide.length || s.explain || Object.values(S.blockCode).some((b) => (b.code || "").trim()); // 내가 한 것이 있을 때만 묻는다
  if (!progressed) return void changeLanguage(language);
  S.langWant = language; // 지워질 것이 있으면 먼저 묻는다
  render();
  $("lang-no").focus();
}

async function startMode() {
  const pid = S.pid, mode = S.mode;
  S.note.start = null;
  const prep = S.problem.preparing || (S.problem.builtin && S.session.strategy == null); // 기본 문제는 열 때 준비하지 않아 계획이 없으면 시작이 준비부터 한다
  const r = await work(prep ? "풀이 순서를 준비하는 중…" : START[mode][3], "start", () => (mode === "explain" ? api("/api/explain", { id: pid }) : api("/api/turn", { id: pid, mode, event: "start" })));
  if (!r || S.pid !== pid) return;
  if (!r.ok && r.error.code !== "already_started") S.note.start = mode !== "explain" && r.error.code === "invalid_output" ? PREP_FAILED : errorNote(r.error);
  say(r.ok ? (mode === "explain" ? "해설이 준비됐어요." : "튜터가 첫 질문을 했어요.") : "");
  await loadState();
}

async function sendAnswer(given) {
  const pid = S.pid, mode = S.mode, text = typeof given === "string" ? given : $("say").value.trim();
  if (!text) { S.note.chat = { type: "warn", text: "답을 적은 뒤 보내 주세요." }; render(); return $("say").focus(); }
  S.note.chat = null;
  S.sending = { text };
  const r = await work("튜터가 생각하는 중…", "chat", () => api("/api/turn", { id: pid, mode, event: "message", text }));
  if (!r || S.pid !== pid) return;
  if (r.ok && typeof given !== "string") $("say").value = "";
  else if (!r.ok) S.note.chat = errorNote(r.error);
  say(r.ok ? "튜터가 답했어요." : "");
  await loadState();
}

/** 결과의 '이 블록 힌트 받기': 튜터 방식 안에서 지금 블록의 다음 힌트를 청한다(‘힌트 주세요’는 튜터가 규칙으로 힌트를 주는 말). */
const tutorHint = () => sendAnswer("힌트 주세요");

async function sendFollowup() {
  const pid = S.pid, mode = S.mode, quote = S.quote, text = $("fq-text").value.trim();
  if (!text) { S.note.chat = { type: "warn", text: "꼬리질문을 적은 뒤 보내 주세요." }; render(); return $("fq-text").focus(); }
  S.note.chat = null;
  S.sending = { text };
  const r = await work("튜터가 꼬리질문에 답하는 중…", "thread", () => api("/api/followup", { id: pid, mode, quote_id: quote, text }));
  if (!r || S.pid !== pid) return;
  if (r.ok) $("fq-text").value = "";
  else S.note.chat = errorNote(r.error);
  say(r.ok ? "튜터가 꼬리질문에 답했어요." : "");
  await loadState();
}

async function fillBlock(blockId) {
  harvest();
  const pid = S.pid, s = S.session, before = s.open_count;
  const filled = s.blocks.filter((b) => b.id !== blockId && ((S.blockCode[b.id] || {}).code || "").trim()).map((b) => ({ id: b.id, code: S.blockCode[b.id].code }));
  S.note.blocks = null;
  await work("블록을 채우는 중…", "blocks", async () => {
    const r = await api("/api/fill", { id: pid, block_id: blockId, filled });
    if (S.pid !== pid) return;
    if (!r.ok) return void (S.note.blocks = errorNote(r.error));
    S.blockCode[blockId] = { code: r.data.code, by: "tutor" };
    saveBlocks();
    if (r.data.note) S.note.blocks = { type: "warn", text: r.data.note }; // 내 이름에 맞춰 채우지 못했거나 확인 전으로 남겼다
    say("블록을 채웠어요.");
    if (r.data.open_count > before) { // 새 블록이 열렸으면 그 블록의 첫 질문을 받는다(모델을 부르지 않는다)
      const next = await api("/api/turn", { id: pid, mode: S.talk, event: "next" });
      if (!next.ok && S.session[S.talk].length) S.note.chat = errorNote(next.error);
    } else if (S.talk === "guide" && blockId === s.blocks[s.blocks.length - 1].id) { // 가이드 마지막 블록을 채웠다: 채운 코드를 확인받아 끝 안내를 대화에 받는다(모델 0회)
      const done = await api("/api/turn", { id: pid, mode: "guide", event: "block_filled", block_id: blockId, code: r.data.code, quiet: true }); // 채운 코드는 '나'의 말이 아니다
      if (!done.ok && S.session.guide.length) S.note.chat = errorNote(done.error);
    }
  });
  if (S.pid === pid) await loadState();
}

/** 블록 코드 확인: 가이드는 지금 블록, 의자는 이미 찾은 블록(맞는지만 알려 주고 진행은 그대로). */
async function checkBlock(blockId) {
  harvest();
  const pid = S.pid, mode = S.talk, block = S.session.blocks.find((b) => b.id === blockId);
  const code = block ? (S.blockCode[block.id] || {}).code || "" : "";
  if (!code.trim()) { S.note.blocks = { type: "warn", text: "이 블록의 코드를 먼저 적어 주세요." }; return render(); }
  S.note.blocks = S.note.chat = null;
  S.sending = { text: code };
  const r = await work("코드를 이어 돌려 보는 중…", "chat", () => api("/api/turn", { id: pid, mode, event: "block_filled", block_id: block.id, code }), "언어에 따라 오래 걸릴 수 있어요");
  if (!r || S.pid !== pid) return;
  if (!r.ok) S.note.chat = errorNote(r.error);
  say(r.ok ? "튜터가 블록 코드를 봤어요." : "");
  await loadState();
  if (r.ok && S.pid === pid) markChecked(block.id, code, r.data);
}

/** 이대로 넘어가기: 확인하지 않고 그 블록을 '확인 전'으로 둔 채 다음 블록을 연다(모델·실행 없이). 실패한 확인에 갇히지 않게 한다. */
async function skipBlock(blockId) {
  harvest();
  const pid = S.pid, mode = S.talk, block = S.session.blocks.find((b) => b.id === blockId);
  const code = block ? (S.blockCode[block.id] || {}).code || "" : "";
  if (!code.trim()) return;
  S.note.blocks = S.note.chat = null;
  const r = await api("/api/turn", { id: pid, mode, event: "block_filled", block_id: block.id, code, skip: true, quiet: true });
  if (S.pid !== pid) return;
  if (!r.ok) S.note.chat = errorNote(r.error);
  say(r.ok ? "확인 전으로 두고 다음 블록을 열었어요." : "");
  await loadState();
  if (r.ok && S.pid === pid) markChecked(block.id, code, r.data, true);
}

/** 끝까지 내 방식으로 쓰기: 이 블록은 넘어가기와 같게 '확인 전'으로 두고 남은 블록을 모두 연다(모델·실행 없이). 이 문제의 튜터 방식 동안 블록 코드 확인을 숨긴다. */
async function ownWayBlock(blockId) {
  harvest();
  const pid = S.pid, block = S.session.blocks.find((b) => b.id === blockId);
  const code = block ? (S.blockCode[block.id] || {}).code || "" : "";
  if (!code.trim()) return;
  S.note.blocks = S.note.chat = null;
  const r = await api("/api/turn", { id: pid, mode: "guide", event: "block_filled", block_id: block.id, code, skip: true, quiet: true, own_way: true });
  if (S.pid !== pid) return;
  if (!r.ok) S.note.chat = errorNote(r.error);
  say(r.ok ? "남은 블록을 모두 열었어요. 다 쓴 뒤 모아서 실행으로 확인해요." : "");
  await loadState();
  if (r.ok && S.pid === pid) markChecked(block.id, code, r.data, true);
}

/** 튜터 차례로 돌아가기: 블록 코드 확인을 다시 보인다(열린 블록과 칸의 글은 그대로). */
async function ownWayOff() {
  const pid = S.pid, r = await api("/api/own_way", { id: pid, on: false });
  if (S.pid !== pid) return;
  if (!r.ok) { S.note.blocks = errorNote(r.error); return render(); }
  S.ownWay = r.data.own_way;
  say("튜터 차례로 돌아왔어요. 블록마다 ‘블록 코드 확인’을 쓸 수 있어요.");
  render();
}

/** 확인 결과를 그 블록 칸 바로 아래 한 줄로 남긴다(누른 곳과 결과가 먼 오른쪽 대화에만 떴다). 통과를 물린 뒤 블록에는 그 표시를.
    블록 칸의 글과 함께 저장해(blocks) 다시 열어도 남는다. 칸 글을 고치면 harvest가 지운다. */
function markChecked(blockId, code, data, skipped) {
  const b = S.session.blocks.find((x) => x.id === blockId), saved = S.blockCode[blockId];
  if (!b || !saved || saved.code !== code) return;
  const said = [...(data.messages || [])].reverse().find((m) => m.role === "service"), text = ((said && said.text) || "").replace(/^이 코드로는 아직 넘어가지 않아요\.\s*/, "");
  const first = (/^[\s\S]*?(?:요|다)\.(?=\s|$)/.exec(text) || [text.split("\n")[0]])[0].trim();
  // 실행이 뒷받침하지 못한 판정(unsure: 결론까지 돌리지 못한 것, 확인 전으로 넘어옴)은 '이어지지 않아요'가 아니라 '확인 전'으로, 그 까닭을 보인다
  saved.line = skipped ? { unsure: true, skipped: true, text: "이대로 넘어갔어요. 이 블록은 확인하지 않았어요." }
    : b.verdict === "Y" ? { ok: true, text: "통과예요" } : data.unsure ? { unsure: true, text: first } : { ok: false, text: first };
  for (const id of data.withdrawn || []) if (S.blockCode[id]) S.blockCode[id].line = { withdrawn: true };
  saveBlocks();
  renderBlocks();
}

/* ── 틀린 곳 같이 찾기 ── */
function renderDebug() {
  const d = S.debug, open = !!(d && d.open);
  $("debug-sheet").hidden = !open;
  if (!open) return;
  let html = d.messages.map((m) => (m.role === "service" ? tutorBubble(m.text) : m.role === "regrade" ? `<p class="regrade" role="separator">${esc(m.text)}</p>` : meMsg(m.text))).join("");
  if (S.busy && S.busy.where === "debug") html += (S.sending ? meMsg(S.sending.text, true) : "") + pending("debug");
  if (d.passed) html += '<div class="note ok" role="status">고친 코드가 모든 케이스를 통과했어요. 채점 결과 칸에서 피드백을 받아 보세요.</div>';
  html += noteHtml(d.note);
  const log = $("debug-log"), key = `${d.messages.length}:${S.busy ? 1 : 0}:${d.passed}:${(d.note || {}).text}`;
  log.innerHTML = html;
  if (log._key !== key) { log._key = key; log.scrollTop = log.scrollHeight; }
  $("debug-composer").hidden = !!d.passed;
}

/** 다시 채점한 결과 한 줄(결과 상자의 제목과 같은 말). */
function judgedLine(j) {
  const score = j.score || { accuracy: [0, 0], efficiency: [0, 0] };
  if (j.ok) return "통과";
  if (!j.cases.length) return "실행하지 못했어요";
  return `${j.many ? MANY_HEAD : slowOnlyOf(j) ? "답은 맞지만 느려요" : "아직 틀려요"} · 정확성 ${score.accuracy[0]}/${score.accuracy[1]}${score.efficiency[1] ? ` · 효율성 ${score.efficiency[0]}/${score.efficiency[1]}` : ""}`;
}

async function debugCall(text) {
  const pid = S.pid, code = $("code").value, d = S.debug;
  d.note = null;
  S.sending = text ? { text } : null;
  const r = await work(text ? "튜터가 답을 읽는 중…" : "튜터가 코드를 보는 중…", "debug", () => api("/api/debug", { id: pid, code, text }));
  if (!r || S.pid !== pid) return;
  if (!r.ok) {
    d.note = errorNote(r.error);
    if (text) { $("debug-say").value = text; d.note = { ...d.note, text: `${d.note.text} 쓴 글은 입력 칸에 그대로 있어요.` }; } // 보낸 글이 사라지지 않게
  } else {
    if (r.data.judged) S.result = r.data.judged;
    d.code = code;
    d.passed = !!r.data.passed;
    // 대화를 바꿔 끼우지 않고 잇는다. 서버 기록(r.data.messages)은 쌓이기만 해서 새로 온 것만 더한다(d.seen: 이미 더한 수)
    const fresh = r.data.messages ? r.data.messages.slice(d.seen || 0) : [...(text ? [{ role: "user", text }] : []), { role: "service", text: r.data.message }];
    if (r.data.messages) d.seen = r.data.messages.length;
    const at = fresh.findIndex((m) => m.role === "service"), regraded = r.data.judged && d.messages.length && !d.passed;
    if (regraded && at >= 0) fresh.splice(at, 0, { role: "regrade", text: `다시 채점했어요: ${judgedLine(r.data.judged)}` }); // 고친 코드를 다시 채점했다: 구분선 아래에 새 질문
    d.messages = d.messages.concat(fresh);
    if (!d.passed) d.line = r.data.efficiency_only ? null : r.data.line;
    $("debug-say").value = "";
    $("code")._seen = code;
  }
  say(!r.ok ? "" : d.passed ? "고친 코드가 통과했어요." : d.line ? `튜터가 ${d.line}번째 줄을 짚었어요.` : "튜터가 물었어요.");
  if (r.ok && r.data.judged) await loadState();
  else render();
}

function debugStart() {
  setCodeTab("direct", "quiet");
  const code = $("code").value, d = S.debug || (S.debug = { messages: [], line: null, code: null, passed: false, note: null });
  d.open = true;
  if (d.messages.length && d.code === code && !d.passed) { render(); return void $("debug-say").focus(); } // 하던 대화를 다시 연다
  d.passed = false;
  debugCall(null).then(() => { if (S.debug && S.debug.open && !S.debug.passed) $("debug-say").focus(); });
}

function debugSend() {
  const text = $("debug-say").value.trim();
  if (!text && $("code").value === S.debug.code) { S.debug.note = { type: "warn", text: "답을 적거나, 코드를 고친 뒤 보내 주세요." }; render(); return $("debug-say").focus(); }
  debugCall(text || null);
}

/* ── 09 피드백 ── */
async function showFeedback(pid) {
  show("feedback");
  $("fb-back").href = `#/p/${pid}`;
  api("/api/report").then((rep) => { // 다음 문제: 학습 보고서가 권하는 것 가운데 이 문제가 아닌 첫 문제
    const nx = rep.ok && nextOf(rep.data.next, pid);
    $("fb-next").href = nx ? `#/p/${nx.id}` : "#/list";
    $("fb-next").textContent = nx ? "다음 문제" : "문제 목록으로";
    $("fb-next").title = nx ? nx.title : "";
  });
  if (S.pid !== pid) clearProblem(pid);
  const want = S.wantFeedback;
  S.wantFeedback = false;
  S.fb = { data: S.fb ? S.fb.data : null, note: null, loading: true };
  render();
  if (!S.problem) await loadState();
  if (S.pid !== pid) return;
  const r = want ? await work("제출한 코드와 이번 풀이의 기록을 읽고 피드백을 쓰는 중…", "feedback", () => api("/api/feedback", { id: pid })) : await api("/api/feedback/get", { id: pid });
  if (!r || S.pid !== pid) return;
  S.fb.loading = false;
  if (r.ok) S.fb.data = r.data;
  else if (want || r.error.code !== "not_found") S.fb.note = errorNote(r.error);
  if (want) say(r.ok ? "피드백이 준비됐어요." : "");
  S.hasFeedback = S.hasFeedback || r.ok;
  render();
}

function renderFeedback() {
  const fb = S.fb || {}, d = fb.data, p = S.problem;
  $("fb-sub").textContent = p ? `${p.title} · ${LANG[p.language] || p.language}` : "";
  const advice = { keep_flow: "지금 흐름을 살려서 고칠 곳", canonical: "정석 순서로 다시 짜 보기" }[d && d.strategy] || "다음에는 이렇게 해 보세요";
  // 분석은 [확실]·[가능성 높음]·[추측]을 그 표시가 가리키는 주장 문장의 앞에 붙여 온다(질문 문장에는 없다).
  // 표시는 뒤따르는 한 문장에 붙이고, 표시 없는 문장(표시 앞의 글, 주장 뒤의 질문)은 표시 없이 한 줄로 그린다
  const claims = (text) => {
    const parts = String(text).split(/\[(확실|가능성 높음|추측)\]/);
    if (parts.length < 3) return rich(text);
    const rows = [["", parts[0]]];
    for (let i = 1; i < parts.length; i += 2) {
      const body = parts[i + 1].trim(), first = (/^[\s\S]*?[.?!](?=\s|$)/.exec(body) || [body])[0];
      rows.push([parts[i], first], ["", body.slice(first.length)]);
    }
    return `<ul class="claims">${rows.filter(([, body]) => body.trim()).map(([word, body]) => `<li><span>${inline(body.trim())}</span>${word ? ` <span class="sure s${{ 확실: 1, "가능성 높음": 2, 추측: 3 }[word]}">${word}</span>` : ""}</li>`).join("")}</ul>`;
  };
  let html = "";
  if (S.busy && S.busy.where === "feedback") html += `<div class="note">${waitLine("feedback").replace("보통 5~25초", "30초에서 1분쯤")}</div>`;
  html += noteHtml(fb.note);
  if (d) {
    html += [["내 생각의 흐름 돌아보기", d.analysis], ["비슷한 문제를 만나면", d.similar_hint], [advice, d.advice]].filter(([, body]) => typeof body === "string" && body)
      .map(([title, body], i) => `<section class="card"><h2>${title}</h2><div class="prose">${(i ? rich : claims)(body)}</div></section>`).join("");
  } else if (!S.busy && !fb.loading) {
    html += '<div class="card"><div class="prose"><p>아직 받은 피드백이 없어요. 코드를 한 번 제출한 뒤에 받을 수 있어요.</p></div><div class="page-actions"><button type="button" id="fb-get" class="btn" data-model>지금 피드백 받기</button></div></div>';
  }
  $("fb-body").innerHTML = html;
  $("fb-again").hidden = !d;
}

function askFeedback() {
  S.wantFeedback = true;
  S.fb = null;
  if (S.view === "feedback") showFeedback(S.pid);
  else location.hash = `#/p/${S.pid}/feedback`;
}

/* ── 연결 ── */
let loginPoll = null;
let CONN = { ready: false, name: "" };
let ACCOUNTS = null;

/* ── 이 기기의 언어 도구: 없는 언어도 고를 수는 있고, 실행·제출만 막는다 ── */
let TOOLS = null; // 언어 → 있음(true)·없음(false). 서버가 채점기와 같은 방법으로 센 것
const noTool = () => !!(TOOLS && S.problem && TOOLS[S.problem.language] === false);

async function loadTools(refresh) {
  const r = await api("/api/tools", { refresh });
  if (!r.ok) return r;
  TOOLS = r.data.tools;
  $("tools-list").innerHTML = Object.entries(TOOLS).map(([key, ok]) => `<li><span>${esc(LANG[key] || key)}</span><span class="state ${ok ? "strong" : "weak"}">${ok ? "있음" : "없음"}</span></li>`).join("");
  if (S.view === "new") fillLangs();
  render();
  return r;
}

/* ── 과정별 모델 ── */
const THEME_HELP = {
  read: "문제를 넣을 때 이미지에서 글을 읽어요.",
  guide: "문제를 넣을 때 한 번: 문제의 뼈대와 풀이 가이드(정답 코드). 뒤의 모든 대화가 이 결과를 따라요.",
  blocks: "문제를 넣을 때 한 번: 풀이를 블록으로 나누고 블록마다 힌트 질문을 만들어요.",
  talk: "튜터가 매번 건네는 말: 질문, 꼬리질문 답, 블록 채우기.",
  judge: "내 답과 블록 코드가 맞는지 보는 짧은 판정.",
  explain: "튜터의 해설.",
  feedback: "제출 뒤의 피드백.",
  debug: "틀린 코드에서 원인이 있는 줄 찾기.",
};
const EFFORT = { low: "낮음", medium: "보통", high: "높음" };

function renderModels() {
  const a = ACCOUNTS;
  $("models-body").innerHTML = a.themes.map((t) => {
    const changed = t.tier !== t.default_tier || t.effort !== t.default_effort;
    return `<section class="theme" aria-labelledby="theme-${t.key}">
      <div class="theme-head"><h3 id="theme-${t.key}">${esc(t.label)}</h3>
        ${changed ? `<button type="button" class="btn quiet small" data-theme="${t.key}" data-pick="" data-effort="" aria-label="${esc(t.label)} 기본값으로">기본값으로</button>` : '<span class="tag">기본값</span>'}</div>
      <p class="hint">${THEME_HELP[t.key]}</p>
      <div class="theme-row"><span class="label">모델</span><div class="picks" role="group" aria-label="${esc(t.label)} 모델">
        ${a.tiers.map((m) => `<button type="button" class="pick" data-theme="${t.key}" data-pick="${m.key}" data-effort="${t.effort}" aria-pressed="${m.key === t.tier}">${esc(m.label)}</button>`).join("")}
      </div></div>
      <div class="theme-row"><span class="label">추론</span><div class="picks" role="group" aria-label="${esc(t.label)} 추론 정도">
        ${Object.entries(EFFORT).map(([key, name]) => `<button type="button" class="pick" data-theme="${t.key}" data-pick="${t.tier}" data-effort="${key}" aria-pressed="${key === t.effort}">${name}</button>`).join("")}
      </div></div>
    </section>`;
  }).join("");
  $("models-note").textContent = a.model ? `개발용 환경 변수 ALGOBLOCK_LLM_MODEL(${a.model})이 있어서, 지금은 모든 과정이 그 모델을 써요.` : "";
}

async function setTheme(theme, tier, effort) {
  const row = ACCOUNTS.themes.find((t) => t.key === theme);
  const r = await api("/api/theme", { theme, tier: tier === row.default_tier ? "" : tier, effort: effort === row.default_effort ? "" : effort });
  if (r.ok) renderAccounts(r.data);
  const now = r.ok && r.data.themes.find((t) => t.key === theme);
  $("models-note").textContent = r.ok ? `저장했어요. ${row.label}: ${now.model_label}, 추론 ${EFFORT[now.effort]}` : errorNote(r.error).text;
}

function openModels() {
  const box = $("models");
  renderModels();
  if (!box.open) box.showModal ? box.showModal() : box.setAttribute("open", "");
  $("models-title").focus();
}
function renderAccounts(a) {
  const provider = a.keys.claude ? "Claude API 키" : a.chatgpt ? "ChatGPT 로그인" : a.keys.openai ? "OpenAI API 키" : "";
  const ready = a.client === "cli" || !!provider;
  CONN = { ready, name: a.client === "cli" ? "이 PC의 Claude Code" : provider };
  ACCOUNTS = a;
  if (!paneTimer && !paneDrag) paneSet(a.panes || null, false); // 저장한 칸 너비를 첫 그림 전에(accounts를 기다린 뒤에 route()를 부른다)
  $("themes-now").textContent = a.themes.map((t) => `${t.label} ${t.model_label}`).join(" · ");
  if ($("models").open) renderModels();
  $("conn-now").textContent = keyBad ? "키 확인 필요" : a.client === "cli" ? "이 PC의 Claude Code" : provider || "연결 안 됨";
  $("conn-dot").classList.toggle("off", !ready);
  $("conn-state").textContent = keyBad ? "넣은 키가 맞지 않아요. 키를 다시 넣어 주세요." : ready ? `지금 연결: ${CONN.name}` : "아직 연결하지 않았어요. 키를 넣으면 튜터를 쓸 수 있어요.";
  $("key-save").classList.toggle("primary", !ready || keyBad);
  $("conn-dot").classList.toggle("warn", keyBad);
  $("conn-now").classList.toggle("warn", keyBad);
  document.querySelector(".dev-conn").hidden = !a.dev; // 개발용 연결로 띄웠을 때만 이 칸이 있다
  document.querySelectorAll('input[name="client"]').forEach((el) => { el.checked = el.value === a.client; });
  renderScheme();
  $("provider-now").textContent = provider ? `지금은 ${provider}` : "아직 없음";
  $("chatgpt-state").textContent = a.chatgpt ? "연결됨 · ChatGPT 요금제를 쓰는 중" : a.chatgpt_note || "연결 안 됨"; // 연결되지 않은 까닭(허락하지 않음, 자격 없음, 다시 로그인 필요)
  $("chatgpt-usage").hidden = !a.chatgpt;
  renderKeyRows();
  renderKeyDelete();
  renderKeyStatus();
  if (a.chatgpt) { clearInterval(loginPoll); $("chatgpt-link").hidden = true; }
  if (S.view === "code" && S.problem) render();
  if (S.view === "list" && $("entries").innerHTML && !!$("note-conn") === ready) showList(); // 홈의 연결 한 줄을 새로 그린다
}

/** 화면 색: 라디오를 고른 값(저장 중이면 그 값, 아니면 저장된 값)에 맞추고 화면에도 적용한다(적용 함수는 index.html 머리에 있다). */
let schemePicked = null; // 방금 고른 값. 늦게 온 /api/accounts 응답이 예전 값으로 되돌리지 못하게 응답보다 앞선다
function renderScheme() {
  const pref = schemePicked || (ACCOUNTS && ACCOUNTS.scheme) || "system";
  document.querySelectorAll('input[name="scheme"]').forEach((el) => { el.checked = el.value === pref; });
  applyScheme(pref);
}
async function chooseScheme(scheme) {
  schemePicked = scheme;
  renderScheme(); // 응답을 기다리지 않고 바로 칠한다
  const r = await accounts("/api/prefs", { scheme }, "");
  if (r.ok) say("화면 색을 바꿨어요.");
  else if (schemePicked === scheme) { schemePicked = null; renderScheme(); } // 저장하지 못했으면 저장돼 있는 값으로 되돌린다(그사이 다른 값을 골랐으면 그대로)
}

const KEY_LABEL = { claude: "Claude", openai: "OpenAI" };
const KEY_PREFIX = { claude: "sk-ant-", openai: "sk-" }; // 서버(KEY_FORM)와 같은 꼴. 저장 전에 서버가 다시 본다
const KEY_CONSOLE = { claude: "https://console.anthropic.com/settings/keys", openai: "https://platform.openai.com/api-keys" }; // 키를 받는 공식 콘솔
const keyName = () => document.querySelector('input[name="keyname"]:checked').value;
/** 지우기 확인은 누른 줄의 공급자 것만 묻는다. 줄이 다시 그려지면(키가 달라지면) 접는다. */
let keyDeleting = null;
function renderKeyDelete() {
  const name = keyDeleting, has = !!(name && ACCOUNTS && ACCOUNTS.keys_saved[name]); // 화면에서 넣은 키만 지울 수 있다(.env·환경 변수의 키는 아니다)
  if (!has) keyDeleting = null;
  $("key-delete-confirm").hidden = !has;
  if (has) $("key-delete-ask").textContent = `이 기기에 넣은 ${KEY_LABEL[name]} 키를 지울까요? 다른 키는 그대로예요.`;
}
/* ── 공급자마다 키 한 줄: 연결됨·안 됨, 끝 4자리, 마지막 확인, 다시 확인, 지우기 ── */
const KEY_RESULT = { ok: ["ok", "쓸 수 있어요"], invalid: ["error", "거절됨 · 키가 틀려요"], denied: ["warn", "권한이 부족해요 · 모델 목록을 볼 수 없어요"],
  limited: ["warn", "키는 맞아요 · 지금은 요청 한도에 걸려 있어요"], server: ["warn", "확인하지 못했어요 · 공급자 서버가 답하지 않았어요"], offline: ["warn", "확인하지 못했어요"] };
const KEY_ICON = { ok: "i-check", error: "i-x", warn: "i-warn", off: "" };
let keyRechecking = null; // 다시 확인하는 중인 공급자
const keyTime = (iso) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("ko-KR", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit" }); };
function keyRowState(a, name) {
  const r = a.key_rows[name];
  if (!r.on) return ["off", "연결 안 됨"];
  if (keyBad && a.using === name) return ["error", "거절됨 · 튜터 요청에서 키가 거절됐어요"]; // 튜터를 부르다 키 오류를 받았다
  return KEY_RESULT[r.result] || ["off", "연결됨 · 아직 확인하지 않았어요"];
}
function renderKeyRows() {
  if (!ACCOUNTS || !ACCOUNTS.key_rows) return;
  const a = ACCOUNTS;
  const html = ["claude", "openai"].map((name) => {
    const r = a.key_rows[name], [kind, text] = keyRowState(a, name), working = keyRechecking === name, using = CONN.ready && a.client !== "cli" && a.using === name && r.on;
    return `<li class="key-item">
      <div class="key-item-head"><strong>${KEY_LABEL[name]} API 키</strong>${using ? '<span class="tag">지금 쓰는 중</span>' : ""}${r.tail ? `<span class="mono muted" title="키의 끝 네 글자">…${esc(r.tail)}</span>` : ""}</div>
      <p class="key-state ${kind}">${KEY_ICON[kind] ? ico(KEY_ICON[kind]) : ""}<span>${esc(working ? "확인하는 중이에요…" : text)}</span></p>
      ${r.at && !working ? `<p class="hint">마지막 확인 ${esc(keyTime(r.at))}</p>` : ""}
      ${r.on ? `<div class="key-item-acts"><button type="button" id="key-recheck-${name}" class="btn small"${keyRechecking || keyChecking ? " disabled" : ""}>다시 확인</button>${a.keys_saved[name] ? `<button type="button" id="key-del-${name}" class="btn quiet small"${keyRechecking || keyChecking ? " disabled" : ""}>지우기</button>` : '<span class="hint">.env나 환경 변수의 키예요</span>'}</div>` : ""}
    </li>`;
  }).join("");
  if ($("key-rows").dataset.sig !== html) { // 같은 줄이면 다시 그리지 않는다(ChatGPT 로그인을 기다리며 3초마다 부를 때 초점이 달아나지 않게)
    $("key-rows").dataset.sig = html;
    $("key-rows").innerHTML = html;
  }
}
function askKeyDelete(name) { keyDeleting = name; renderKeyDelete(); $("key-delete-no").focus(); }
async function recheckKey(name) {
  if (keyRechecking || keyChecking) return; // 키를 넣는 중이면 다시 확인하지 않는다(서로 기다린다)
  keyRechecking = name;
  renderKeyStatus();
  const r = await api("/api/key/check", { name });
  keyRechecking = null;
  if (r.ok) {
    renderAccounts(r.data);
    if (r.data.key_check === "invalid") KEYUI[name] = null; // 키가 틀렸다: 칸 아래의 옛 결과(쓸 수 있어요)는 걷는다
    if (ACCOUNTS.using === name && ["ok", "limited"].includes(r.data.key_check)) setKeyBad(false); // 키가 맞다고 확인됐다
    else if (ACCOUNTS.using === name && r.data.key_check === "invalid") setKeyBad(true); // 지금 쓰는 키가 거절되면 머리의 '키 확인 필요'도 따른다. 확인하지 못한 것은 그대로 둔다
    const [, text] = KEY_RESULT[r.data.key_check] || ["", "확인하지 못했어요"];
    say(`${KEY_LABEL[name]} 키를 다시 확인했어요. ${text}`);
  } else $("conn-note").textContent = errorNote(r.error).text;
  renderKeyStatus();
  const again = $(`key-recheck-${name}`);
  if (again) again.focus();
}
/* ── 키 칸의 상태: 비어 있음 → 입력 중(꼴 맞음·틀림) → 확인하는 중 → 쓸 수 있어요 / 거절됨 / 확인하지 못함. 공급자마다 마지막 결과를 따로 둔다 ── */
const KEYUI = { claude: null, openai: null }; // {kind: ok·warn·error, text, retry, raw}. raw: 그 결과를 받은 때의 입력(입력이 달라지면 그 결과는 보이지 않는다)
let keyChecking = false;
/** 입력한 키의 꼴이 맞지 않으면 까닭을, 맞으면 "". */
function keyFormBad(name, raw) {
  const v = raw.trim(), label = KEY_LABEL[name], prefix = KEY_PREFIX[name];
  if (/\s|[^\x21-\x7e]/.test(v)) return "빈칸이나 한글이 섞여 있어요. 키만 붙여 넣어 주세요.";
  if (name === "openai" && v.startsWith("sk-ant-")) return "Claude 키 같아요. 위에서 Claude 키를 골라 주세요.";
  if (!v.startsWith(prefix)) return `${label} 키는 ${prefix}로 시작해요.`;
  if (v.length > 400 || !/^[A-Za-z0-9_-]+$/.test(v)) return "키에는 영문, 숫자, -, _만 있어요.";
  return "";
}
/** 입력한 키를 보이게(true)·가리게(false). 저장하거나 공급자를 바꾸거나 창을 닫으면 가린 상태로 돌린다. */
function setKeyShown(show) {
  $("key-value").type = show ? "text" : "password";
  $("key-reveal").textContent = show ? "숨기기" : "보기";
  $("key-reveal").setAttribute("aria-pressed", String(show));
}
function renderKeyStatus() {
  const name = keyName(), label = KEY_LABEL[name], raw = $("key-value").value.trim(), box = $("key-status"), saved = KEYUI[name];
  let kind = "", icon = "", text = "", retry = false;
  if (keyChecking) text = `${label}에 키를 확인하는 중이에요…`;
  else if (saved && saved.raw === raw) ({ kind, text, retry } = saved);
  else if (!raw) text = ACCOUNTS && ACCOUNTS.keys[name] ? "키를 바꾸려면 새 키를 붙여 넣어 주세요." : "아직 키를 넣지 않았어요.";
  else { const bad = keyFormBad(name, raw); kind = bad ? "error" : "form"; text = bad || `키 꼴이 맞아요. ‘키 넣기’를 누르면 ${label}에 확인해요.`; }
  icon = keyChecking ? DOTS : kind === "ok" || kind === "form" ? ico("i-check") : kind === "error" ? ico("i-x") : kind === "warn" ? ico("i-warn") : "";
  const sig = `${name}|${keyChecking}|${kind}|${text}|${retry}`;
  if (box.dataset.sig !== sig) { // 같은 글이면 다시 그리지 않는다(글자를 칠 때마다 화면 읽기 도구가 같은 글을 읽지 않게)
    box.dataset.sig = sig;
    box.className = `note${kind === "ok" ? " ok" : kind === "error" ? " error" : kind === "warn" ? " warn" : ""}`;
    box.innerHTML = `${icon}<span>${esc(text)}</span>${retry ? '<button type="button" id="key-retry" class="btn small">다시 시도</button><button type="button" id="key-force" class="btn small">그래도 저장</button>' : ""}`;
  }
  $("key-label").textContent = `${label} API 키`; // 칸 위의 이름표와 안내는 고른 공급자를 따른다
  $("key-prefix").textContent = `${KEY_PREFIX[name]}로 시작해요.`;
  $("key-get").href = KEY_CONSOLE[name];
  $("key-get").textContent = `${label} 콘솔에서 키 받기`;
  $("key-save").disabled = keyChecking || !!keyRechecking;
  document.querySelectorAll('input[name="keyname"]').forEach((el) => { el.disabled = keyChecking; });
  renderKeyRows(); // 줄의 단추도 넣는 중·다시 확인하는 중에 같이 잠근다
}
/** 키를 넣는다: 서버가 공급자에 확인한 뒤 쓸 수 있을 때만 저장한다. 확인하지 못했을 때는 force로 그래도 저장한다. */
async function saveKey(force) {
  const name = keyName(), value = $("key-value").value;
  if (keyChecking || keyRechecking) return;
  const bad = value.trim() ? keyFormBad(name, value) : "키를 붙여 넣어 주세요.";
  if (bad) { KEYUI[name] = { kind: "error", text: bad, raw: value.trim() }; renderKeyStatus(); return void $("key-value").focus(); }
  KEYUI[name] = null;
  keyChecking = true;
  renderKeyStatus();
  const r = await api("/api/key", { name, value, ...(force ? { force: true } : {}) });
  keyChecking = false;
  if (r.ok) {
    $("key-value").value = "";
    setKeyShown(false);
    KEYUI[name] = r.data.key_check === "ok" ? { kind: "ok", text: "쓸 수 있는 키예요. 저장했어요.", raw: "" }
      : r.data.key_check === "limited" ? { kind: "warn", text: "키는 맞아요. 지금은 요청 한도에 걸려 있어요. 저장했어요.", raw: "" } // 429: 키는 맞다
      : { kind: "warn", text: "확인하지 못했지만 저장했어요. 튜터를 처음 부를 때 다시 확인해요.", raw: "" };
    renderAccounts(r.data);
  } else {
    const unverified = ["key_unverified", "key_denied"].includes(r.error.code); // 확인하지 못함·권한 없음: 다시 시도하거나 그래도 저장할 수 있다
    KEYUI[name] = { kind: unverified ? "warn" : "error", text: r.error.message || errorNote(r.error).text, retry: unverified, raw: value.trim() };
  }
  renderKeyStatus();
  if (!r.ok) ($("key-retry") || $("key-value")).focus();
}

async function deleteKey() {
  const name = keyDeleting;
  if (!name) return;
  $("key-delete-yes").disabled = $("key-delete-no").disabled = true; // 요청 중에는 다시 누르지 못하게
  const r = await accounts("/api/key/delete", { name }, `${KEY_LABEL[name]} 키를 지웠어요.`);
  $("key-delete-yes").disabled = $("key-delete-no").disabled = false;
  keyDeleting = null;
  if (r.ok) { KEYUI[name] = null; renderKeyStatus(); }
  renderKeyDelete();
  if (r.ok && ACCOUNTS.keys[name]) $("conn-note").textContent = `${KEY_LABEL[name]} 키를 지웠어요. 그래도 .env나 환경 변수에 키가 있어 계속 연결돼 있어요.`;
  $("conn-toggle").focus();
}

async function accounts(path, body, done) {
  const r = await api(path || "/api/accounts", body);
  if (r.ok) renderAccounts(r.data);
  if (path) $("conn-note").textContent = r.ok ? done : errorNote(r.error).text;
  if (r.ok && $("tour").open) renderTour();
  return r;
}

/* ── 처음 안내: 여섯 장. 장마다 글과 단추만 바꾼다. 연결 없이도 풀 수 있다는 것부터 말한다.
   그림은 움직이는 데모(stageshow/에서 미리 빌드한 tour-demos.js, React)이고, 안내를 처음 열 때만 불러온다.
   못 불러오면 index.html의 정적 그림이 그대로 보인다 ── */
const TOUR = [
  ["홈에서 시작해요", "홈 맨 위에 입구가 셋 있어요. ‘문제 풀기’는 이어서 풀 문제를 열고, ‘내 문제 넣기’는 가진 문제를 넣고, ‘내 기록’은 학습 보고서로 가요. AI를 연결하지 않아도 풀고 바로 채점받을 수 있어요."],
  ["어떻게 풀지 골라요", "문제를 열면 오른쪽에서 푸는 방식을 골라요. ‘혼자 풀기’는 튜터 없이 풀고 막히면 힌트를 봐요. ‘튜터와 차례로’는 풀이를 블록으로 나눠 하나씩 열어 주고, ‘튜터의 질문으로’는 답 대신 질문으로 이끌어요."],
  ["결과 바로 아래에 다음 할 일", "제출하면 결과 아래에 할 일이 하나 나와요. 틀리면 ‘틀린 곳 같이 찾기’나 ‘풀이 힌트 보기’, 통과하면 ‘다음 문제’예요. 통과한 문제는 실전 신호가 열려 비슷한 문제를 알아보는 눈을 길러요."],
  ["내 문제 넣기는 세 걸음", "글을 붙여 넣거나 사진·PDF를 넣고(1 글 넣기), 읽은 글과 자동으로 채운 예시를 확인한 뒤(2 확인하기), 등록해요(3 등록). 등록한 문제도 같은 방식으로 채점해요."],
  ["학습 보고서로 약한 곳을 찾아요", "제출 기록에서 강한 주제와 더 공부할 주제, 자주 하는 실수를 모아 보여 주고, 더 공부할 문제를 바로 열어 줘요."],
  ["AI 연결은 선택이에요", "튜터는 언어 모델로 움직여요. 쓰려면 오른쪽 위 ‘연결’에서 Claude나 OpenAI 키를 넣거나 ChatGPT로 로그인해요. 키는 이 기기에만 저장해요."],
];
let tourAt = 0;
let tourDemos = null; // 데모 묶음을 불러오는 약속(한 번만 부른다). 실패하면 null로 풀린다
let tourShown = -1; // 지금 데모로 틀고 있는 장. 연결 상태만 새로 그릴 때 데모를 처음부터 다시 틀지 않으려고 둔다
let tourRun = 0; // 안내를 열고 닫을 때마다 늘린다. 불러오기가 끝났을 때 그사이 닫혔거나 다시 열렸으면 데모를 올리지 않는다

function loadTourDemos() {
  tourDemos ||= new Promise((done) => {
    const css = Object.assign(document.createElement("link"), { rel: "stylesheet", href: "tour-demos.css" });
    const js = Object.assign(document.createElement("script"), { src: "tour-demos.js" });
    let left = 2;
    const loaded = () => { if (--left === 0) done(window.AlgoBlockTourDemos || null); };
    css.onload = js.onload = loaded;
    css.onerror = js.onerror = () => done(null);
    document.head.append(css, js);
  });
  return tourDemos;
}

async function playTourDemo() {
  const run = tourRun, at = tourAt;
  const demos = await loadTourDemos();
  if (!demos || !$("tour").open || run !== tourRun || at !== tourAt || tourShown === tourAt) return; // 기다리는 사이 닫았거나 장을 넘겼다
  if (!demos.has || !demos.has(tourAt)) { tourShown = -1; $("tour-art").classList.remove("live"); return void demos.clear($("tour-live")); } // 이 장은 정적 그림(새 화면)
  tourShown = tourAt;
  $("tour-art").classList.add("live");
  demos.show($("tour-live"), tourAt);
}

function renderTour() {
  const last = tourAt === TOUR.length - 1;
  document.querySelectorAll(".tour-scene").forEach((el) => { el.hidden = Number(el.dataset.scene) !== tourAt; });
  $("tour-count").textContent = `${tourAt + 1} / ${TOUR.length}`;
  $("tour-title").textContent = TOUR[tourAt][0];
  $("tour-body").textContent = TOUR[tourAt][1] + (!last ? "" : CONN.ready ? ` 지금은 ‘${CONN.name}’ 연결을 쓰고 있어요.` : " 지금은 연결 없이 시작해요. 나중에 언제든 연결할 수 있어요.");
  $("tour-dot").classList.toggle("off", !CONN.ready);
  $("tour-conn").textContent = CONN.ready ? "연결됨" : "연결 안 됨";
  $("tour-dots").innerHTML = TOUR.map((_, i) => `<i${i === tourAt ? ' class="on"' : ""}></i>`).join("");
  $("tour-prev").hidden = tourAt === 0;
  $("tour-skip").textContent = last ? (CONN.ready ? "닫기" : "연결하기") : "건너뛰기"; // 마지막 장에도 닫는 길이 있다
  $("tour-next").textContent = last ? "시작하기" : "다음";
  if ($("tour").open) playTourDemo();
}

function openTour() {
  const tour = $("tour");
  tourAt = 0;
  tourRun += 1;
  renderTour();
  if (!tour.open) tour.showModal ? tour.showModal() : tour.setAttribute("open", "");
  playTourDemo();
  $("tour-title").focus();
}

function closeTour() {
  const tour = $("tour");
  stopTourDemo();
  tour.close ? tour.close() : (tour.removeAttribute("open"), api("/api/tour"));
}

function stopTourDemo() { // 닫으면 올린 데모를 반드시 내린다(뒤에서 돌지 않게). Esc로 닫으면 close 이벤트가 부른다
  tourRun += 1;
  tourShown = -1;
  $("tour-art").classList.remove("live");
  if (window.AlgoBlockTourDemos) window.AlgoBlockTourDemos.clear($("tour-live"));
}

async function tourStep(by) {
  if (tourAt + by >= TOUR.length) { // 마지막 장의 단추: 홈(입구 셋)으로 간다
    closeTour();
    return void (location.hash = "#/list");
  }
  tourAt = Math.max(0, tourAt + by);
  renderTour();
  $("tour-title").focus();
}

/* ── 업데이트: 새 버전 알림 → 받기(진행 %) → 다시 시작해 바꾸기. 확인·받기·검증·바꾸기는 서버(updater.py)가 한다 ── */
let UPD = null; // 마지막으로 받은 업데이트 상태
let updPoll = null;
const UPD_BUSY = ["downloading", "installing", "restarting"];
async function updAct(action, extra) {
  const r = await api("/api/update", { action, ...extra });
  if (r.ok) renderUpdate(r.data);
  else if (!(UPD && UPD.state === "restarting")) $("upd-msg").textContent = errorNote(r.error).text; // 다시 켜는 중에 끊긴 것은 알리지 않는다
  return r;
}
function renderUpdate(u) {
  UPD = u;
  const v = u.latest && u.latest.version;
  const busy = UPD_BUSY.includes(u.state);
  const top = $("upd-open");
  top.hidden = !(v && (busy || u.state === "ready" || v !== u.skip)); // 건너뛴 버전은 막대에 띄우지 않는다('지금 확인'으로는 연다)
  top.textContent = u.state === "downloading" ? `업데이트 받는 중 ${u.progress}%` : u.state === "ready" && u.can_install ? "다시 시작해 업데이트" : busy ? "업데이트하는 중" : `새 버전 ${v} · 업데이트`;
  $("upd-now").textContent = `지금 버전 ${u.current}` + (v ? ` · 새 버전이 나왔어요(${v})` : u.state === "latest" ? " · 최신 버전이에요" : "");
  $("upd-auto").checked = u.auto;
  $("upd-title").textContent = v ? `새 버전 ${v}` : "업데이트";
  $("upd-sub").textContent = `지금 쓰는 버전: ${u.current}`;
  const actions = (...buttons) => `<div class="upd-actions">${buttons.join("")}</div>`;
  let body;
  if (!v) body = "<p>지금이 최신 버전이에요.</p>";
  else if (!u.frozen) body = "<p>소스에서 실행 중이라 여기서 바꾸지 않아요. 저장소에서 git으로 새 버전을 받아 주세요(<code>git pull</code>).</p>";
  else if (!u.latest.asset) body = "<p>이 버전에는 이 기기에 맞는 설치 파일이 없어요.</p>";
  else if (u.state === "downloading") body = `<p>내려받는 중이에요 · ${u.progress}%</p><progress max="100" value="${u.progress}" aria-label="내려받기"></progress>`;
  else if (u.state === "installing") body = "<p>새 버전으로 바꾸는 중이에요. 곧 앱이 꺼졌다가 다시 켜져요.</p>";
  else if (u.state === "restarting") body = "<p>앱을 다시 켜는 중이에요.</p>";
  else if (u.state === "ready" && u.can_install) body = "<p>내려받고 파일이 맞는지 확인했어요. 다시 시작하면 새 버전으로 바뀌어요. 쓰던 코드는 저장하고 끝내요.</p>" + actions('<button type="button" id="upd-install" class="btn primary">다시 시작해 업데이트</button>');
  else if (u.state === "ready") body = `<p>받은 파일: <code>${esc(u.file)}</code></p>` + actions('<button type="button" id="upd-reveal" class="btn">파일 위치 열기</button>');
  else body = `<p>새 버전을 내려받아 바꿀 수 있어요(${Math.max(1, Math.round(u.latest.size / 1048576))}MB).</p>`
    + actions(`<button type="button" id="upd-get" class="btn primary">${u.state === "failed" ? "다시 받기" : "내려받기"}</button>`, v !== u.skip ? '<button type="button" id="upd-skip" class="btn quiet">이 버전 건너뛰기</button>' : "");
  if (v) body += `<p><a class="link" href="${esc(u.latest.notes)}" target="_blank" rel="noopener">바뀐 점 보기</a></p>`;
  $("upd-body").innerHTML = body;
  if ($("upd-msg").textContent !== (u.message || "")) $("upd-msg").textContent = u.message || "";
  clearTimeout(updPoll);
  if (busy) updPoll = setTimeout(() => updAct("status"), 1000);
}
function openUpdate() {
  const box = $("upd");
  if (!box.open) box.showModal ? box.showModal() : box.setAttribute("open", "");
  $("upd-title").focus();
}
const closeUpdate = () => { $("upd").close ? $("upd").close() : $("upd").removeAttribute("open"); };

function toggleConn(open) {
  $("conn-panel").hidden = !open;
  document.body.classList.toggle("conn-open", open); // 연결 창이 떠 있는 동안 주 동작은 창 안의 것 하나
  $("conn-toggle").setAttribute("aria-expanded", open ? "true" : "false");
  if (!open) setKeyShown(false); // 창을 닫으면 입력한 키는 다시 가린다
  if (open) { $("conn-note").textContent = $("tools-note").textContent = ""; accounts(); loadTools(false); $("conn-close").focus(); } else $("conn-toggle").focus();
}

async function chatgptLogin() {
  const r = await api("/api/chatgpt/login");
  if (!r.ok) return void ($("conn-note").textContent = errorNote(r.error).text);
  $("chatgpt-link").href = r.data.url;
  $("chatgpt-link").hidden = false;
  $("conn-note").textContent = "‘브라우저에서 로그인 열기’를 눌러 로그인하고 허락하면 여기에 연결됨으로 바뀌어요.";
  clearInterval(loginPoll);
  let left = 100; // 로그인 창구는 5분 열려 있다
  loginPoll = setInterval(() => { if (--left < 0 || $("conn-panel").hidden) clearInterval(loginPoll); else accounts(); }, 3000);
}

/* ── 글상자: Tab 들여쓰기, Enter 때 들여쓰기 잇기 ── */
// 들여쓰기 한 단계: 그 줄이 탭으로 들여 쓰였으면(줄이 들여 쓰이지 않았으면 탭으로 들여 쓴 줄이 있는 파일이면) 탭 하나, 아니면 공백 4칸(Go 시작 코드는 탭)
const indentUnit = (ta, line) => (/^\t/.test(line) || (!/^\s/.test(line) && /^\t/m.test(ta.value)) ? "\t" : "    ");
function codeKeys(e) {
  const ta = e.target;
  if (e.isComposing || e.ctrlKey || e.metaKey || e.altKey || ta.readOnly) return;
  if (e.key === "Escape") return void (ta._tabOut = true); // Esc 다음 Tab은 다음 칸으로 간다(키보드로 빠져나가는 길)
  const at = ta.selectionStart, lineStart = ta.value.lastIndexOf("\n", at - 1) + 1;
  const line = ta.value.slice(lineStart, (ta.value.indexOf("\n", at) + 1 || ta.value.length + 1) - 1), unit = indentUnit(ta, line);
  if (e.key === "Tab") {
    if (ta._tabOut) return void (ta._tabOut = false);
    e.preventDefault();
    if (!e.shiftKey) ta.setRangeText(unit, at, ta.selectionEnd, "end");
    else {
      const lead = /^(\t| {1,4})/.exec(line);
      if (lead) { ta.setRangeText("", lineStart, lineStart + lead[0].length, "start"); ta.selectionStart = ta.selectionEnd = Math.max(lineStart, at - lead[0].length); }
    }
  } else if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    const before = ta.value.slice(lineStart, at);
    ta.setRangeText("\n" + /^\s*/.exec(before)[0] + (/[{([:]\s*$/.test(before) ? unit : ""), at, ta.selectionEnd, "end"); // 여는 괄호·콜론 다음 줄은 한 단계 더
  } else if (e.key === "Backspace" && ta.selectionStart === ta.selectionEnd && / $/.test(ta.value.slice(0, at)) && !/[^ \t]/.test(ta.value.slice(lineStart, at))) {
    // 줄 앞 공백 안(또는 바로 뒤)의 Backspace: 한 칸이 아니라 이전 들여쓰기 자리까지. 폭은 이 파일에서 가장 얕은 들여쓰기(없으면 4). 탭 뒤의 공백은 탭 다음부터 센다
    e.preventDefault();
    const start = lineStart + ta.value.slice(lineStart, at).lastIndexOf("\t") + 1, rows = ta.value.split("\n");
    const here = ta.value.slice(0, lineStart).split("\n").length - 1;
    const widths = rows.filter((x, i) => i !== here && x.trim()).map((x) => /^ */.exec(x)[0].length).filter((n) => n > 0);
    const step = widths.length ? Math.min(...widths) : 4;
    ta.setRangeText("", start + Math.floor((at - start - 1) / step) * step, at, "end");
  } else {
    return void (ta._tabOut = false);
  }
  ta._tabOut = false;
  ta.dispatchEvent(new Event("input", { bubbles: true }));
}

function grow(ta) {
  ta.style.height = "auto";
  ta.style.height = `${Math.min(ta.scrollHeight + 2, 240)}px`;
}

/* ── 칸 너비: 칸 사이 경계(.sep)를 끌거나 글쇠로 옮긴다. 세 칸의 몫(합 100)을 서버에 적어 다시 켜도 남는다 ── */
const PANE = ["problem", "code", "tutor"], PANE_NAME = ["문제", "코드"];
const PANE_DEFAULT = [25.83, 37.75, 36.42]; // 저장한 값이 없을 때의 몫. CSS 기본(0.78 : 1.14 : 1.1)과 같은 비율
let paneShares = null; // 문제·코드·튜터 칸의 몫. null이면 CSS 기본 배치
let paneTimer = null, paneDrag = null;
const paneWidth = (i) => $(`pane-${PANE[i]}`).getBoundingClientRect().width;
const paneMin = (i) => parseFloat(getComputedStyle($("panes")).getPropertyValue(`--min-${PANE[i]}`)); // 최소 너비는 CSS의 한 곳(--min-*)에서 읽는다
const narrowPanes = () => matchMedia("(max-width: 1179px)").matches; // 문제 칸이 위 띠가 되어 코드·튜터 둘만 나뉜다

/** 경계 하나가 가르는 두 칸의 지금 모습: 왼쪽 칸 번호, 오른쪽 몫(혼자 풀기에서는 코드와 튜터가 한 몫), 몫, 두 칸 너비의 합(px), 최소 너비 */
function paneBase(sep) {
  const left = sep.id === "sep-problem" ? 0 : 1, classes = $("panes").classList, railed = classes.contains("railed");
  const width = PANE.map((_, i) => paneWidth(i));
  let shares = (paneShares || PANE_DEFAULT).slice();
  if (!railed && !classes.contains("folded") && !narrowPanes()) { // 세 칸이 모두 몫으로 나뉠 때는 보이는 너비에서 다시 잡는다(최소 너비에 걸린 채 시작해도 손잡이가 포인터를 따라오게)
    const total = width[0] + width[1] + width[2];
    shares = [round2(100 * width[0] / total), round2(100 * width[1] / total)];
    shares.push(round2(100 - shares[0] - shares[1]));
  }
  const right = left === 0 && railed ? [1, 2] : [left + 1];
  return { left, right, shares, from: width[left], span: width[left] + width[left + 1], min: [paneMin(left), paneMin(left + 1)], sum: shares[left] + right.reduce((n, i) => n + shares[i], 0) };
}

/* pane-pure:start (DOM을 읽지 않는 계산. test_server.py가 이 둘레를 떼어 서버가 받는 범위와 맞는지 본다) */
const round2 = (x) => Math.round(x * 100) / 100;

/** 세 몫을 서버가 받는 범위(각각 5에서 90, 합 100)로 맞춘다. 범위 밖으로 나간 만큼은 keep(끈 칸)이 아닌 칸이 여유가 큰 쪽부터 받는다 */
function paneFit(shares, keep) {
  const out = shares.map((x) => Math.min(90, Math.max(5, x)));
  let diff = 100 - out[0] - out[1] - out[2];
  const order = [0, 1, 2].filter((i) => i !== keep).sort((a, b) => (diff > 0 ? out[a] - out[b] : out[b] - out[a]));
  order.push(keep);
  for (const i of order) {
    const step = Math.min(90, Math.max(5, out[i] + diff)) - out[i];
    out[i] += step;
    diff -= step;
  }
  const fit = out.map(round2), room = fit.map((x) => Math.min(x - 5, 90 - x));
  const at = room.indexOf(Math.max(...room)); // 반올림 오차는 여유가 가장 큰 칸이 받는다
  fit[at] = round2(fit[at] + 100 - fit[0] - fit[1] - fit[2]);
  return fit;
}

/** 왼쪽 칸을 want(px)로 옮긴 몫을 돌려준다. 두 칸의 최소 너비 밖으로는 가지 않는다. 두 칸 밖의 몫은 되도록 그대로다 */
function paneNext(b, want) {
  const left = Math.min(Math.max(want, b.min[0]), Math.max(b.min[0], b.span - b.min[1]));
  const next = b.shares.slice(), mine = round2(b.sum * left / b.span), rest = b.sum - mine;
  next[b.left] = mine;
  if (b.right.length === 1) next[b.right[0]] = rest;
  else { next[1] = rest * b.shares[1] / (b.shares[1] + b.shares[2]); next[2] = rest - next[1]; }
  return paneFit(next, b.left);
}
/* pane-pure:end */

function paneMove(b, want, save) {
  paneSet(paneNext(b, want), save);
}

/** 몫을 화면에 적는다(null이면 기본). save가 참이면 잠깐 뒤 서버에 한 번 적는다 */
function paneSet(shares, save) {
  paneShares = shares;
  const style = $("panes").style, now = shares && { problem: shares[0], code: shares[1], tutor: shares[2], "code-wide": round2(shares[1] + shares[2]) };
  for (const name of [...PANE, "code-wide"]) now ? style.setProperty(`--col-${name}`, `${now[name]}fr`) : style.removeProperty(`--col-${name}`);
  $("panes-reset").hidden = !shares;
  paneAria();
  if (!save) return;
  clearTimeout(paneTimer);
  paneTimer = setTimeout(paneSave, 400);
}

async function paneSave() {
  clearTimeout(paneTimer);
  paneTimer = null;
  const r = await api("/api/prefs", { panes: paneShares });
  if (!r.ok) say(errorNote(r.error).text);
}

function paneReset() {
  paneSet(null, true);
  say("칸 너비를 기본으로 돌렸어요.");
}

/** 손잡이의 값(왼쪽 칸이 두 칸의 합에서 차지하는 %)을 읽어 주는 도구에 알린다 */
function paneAria() {
  for (const sep of document.querySelectorAll(".sep")) {
    if (!sep.getClientRects().length) continue;
    const b = paneBase(sep), pct = (px) => Math.round(100 * px / b.span), now = pct(b.from);
    sep.setAttribute("aria-valuenow", now);
    sep.setAttribute("aria-valuemin", pct(b.min[0]));
    sep.setAttribute("aria-valuemax", pct(Math.max(b.min[0], b.span - b.min[1])));
    sep.setAttribute("aria-valuetext", `${PANE_NAME[b.left]} 칸 ${now}%`);
  }
}

function paneKey(e) {
  if (e.ctrlKey || e.metaKey || e.altKey) return false;
  const b = paneBase(e.target), step = e.shiftKey ? 96 : 24;
  const want = { ArrowLeft: b.from - step, ArrowRight: b.from + step, Home: 0, End: Infinity }[e.key];
  if (want === undefined) return false; // 다루지 않는 키(Esc 등)는 다른 곳으로 넘긴다
  e.preventDefault();
  paneMove(b, want, true);
  return true;
}

/** 끌기를 마친다. cancel이면 끌기 전 너비로 되돌린다(Esc·포인터를 빼앗길 때) */
function paneEnd(e, cancel) {
  const d = paneDrag;
  if (!d || (e.pointerId !== undefined && e.pointerId !== d.id)) return;
  paneDrag = null;
  cancelAnimationFrame(d.frame);
  d.sep.classList.remove("dragging");
  document.body.classList.remove("resizing");
  try { d.sep.releasePointerCapture(d.id); } catch { /* 이미 놓았다 */ }
  if (cancel) return paneSet(d.before, false);
  if (!d.moved) return; // 누르기만 했다(두 번 누르기의 첫 번째 같은)
  if (e.clientX === d.x) return paneSet(d.before, false); // 처음 자리로 돌아와 놓았다. 프레임에 적힌 너비를 걷는다
  paneMove(d.base, d.base.from + e.clientX - d.x, true);
}

document.addEventListener("pointerdown", (e) => {
  const sep = e.target.closest && e.target.closest(".sep");
  if (!sep || e.button !== 0 || paneDrag) return;
  e.preventDefault(); // 글자 선택이 시작되지 않게
  sep.focus();
  sep.setPointerCapture(e.pointerId);
  paneDrag = { sep, id: e.pointerId, x: e.clientX, base: paneBase(sep), before: paneShares && paneShares.slice(), frame: 0 };
  sep.classList.add("dragging");
  document.body.classList.add("resizing");
});
document.addEventListener("pointermove", (e) => {
  const d = paneDrag;
  if (!d || e.pointerId !== d.id) return;
  d.at = e.clientX;
  d.moved = true;
  if (!d.frame) d.frame = requestAnimationFrame(() => { d.frame = 0; paneMove(d.base, d.base.from + d.at - d.x, false); }); // 한 프레임에 한 번
});
document.addEventListener("pointerup", (e) => paneEnd(e, false));
document.addEventListener("pointercancel", (e) => paneEnd(e, true));
document.addEventListener("dblclick", (e) => { if (e.target.closest && e.target.closest(".sep")) paneReset(); });
new ResizeObserver(paneAria).observe($("panes")); // 창이 바뀌거나 칸이 접히고 펴져도 값이 맞게
for (const name of PANE) new ResizeObserver(paneAria).observe($(`pane-${name}`));

/* ── 이벤트 ── */
document.addEventListener("click", (e) => {
  const el = e.target.closest("button");
  if (!el || el.disabled) return;
  if (el.dataset.langFilter !== undefined) { // 등록한 문제를 언어로 거른다(화면에서만)
    LIST_LANG = el.dataset.langFilter;
    document.querySelectorAll("#list-body [data-lang]").forEach((li) => { li.hidden = !!LIST_LANG && li.dataset.lang !== LIST_LANG; });
    return void document.querySelectorAll("[data-lang-filter]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.langFilter === LIST_LANG)));
  }
  if (el.dataset.quote) { S.quote = S.quote === el.dataset.quote ? null : el.dataset.quote; S.note.chat = null; render(); return void (S.quote && $("fq-text").focus()); }
  if (el.dataset.fill) { // 칸에 적은 것이 있으면 바꿀지 먼저 묻는다
    harvest();
    if (!((S.blockCode[el.dataset.fill] || {}).code || "").trim()) return void fillBlock(el.dataset.fill);
    S.fillAsk = el.dataset.fill;
    render();
    return void document.querySelector(`[data-fill-no="${CSS.escape(S.fillAsk)}"]`).focus();
  }
  if (el.dataset.fillYes) { S.fillAsk = null; return void fillBlock(el.dataset.fillYes); }
  if (el.dataset.fillNo) { S.fillAsk = null; render(); return void document.querySelector(`[data-fill="${CSS.escape(el.dataset.fillNo)}"]`).focus(); }
  if (el.dataset.check) return void checkBlock(el.dataset.check);
  if (el.dataset.skip) return void skipBlock(el.dataset.skip);
  if (el.dataset.own) return void ownWayBlock(el.dataset.own);
  if (el.hasAttribute("data-own-off")) return void ownWayOff();
  if (el.dataset.theme) return void setTheme(el.dataset.theme, el.dataset.pick, el.dataset.effort);
  if (el.closest("#more .more-menu") && el.id !== "reset") $("more").open = false; // 더 보기에서 고르면 닫는다. 처음부터의 물음만 그 단추 자리에서 묻는다
  if (el.dataset.way) { // 어떻게 풀까요: 고르면 그 방식으로(튜터는 시작 단추에 초점)
    const way = el.dataset.way;
    return void Promise.resolve(setMode(way, true)).then(() => (tutorWay(way) ? ($("start") && !$("start-box").hidden ? $("start") : $("say")) : $("code")).focus()); // 혼자 풀기는 편집기에, 튜터는 시작 단추에
  }
  if (el.dataset.soloOpen || el.dataset.solo) { S.soloOpen = el.dataset.soloOpen || el.dataset.solo; render(); return void $(`solo-tab-${S.soloOpen}`).focus(); }
  if (el.dataset.tab) { S.keptNote = false; if (!setCodeTab(el.dataset.tab, "tab")) render(); return; }
  if (el.dataset.fileDrop) { // 한 장을 빼도 나머지는 남는다
    const i = Number(el.dataset.fileDrop), [gone] = FILES.splice(i, 1);
    if (gone.file) URL.revokeObjectURL(gone.url);
    filesTouched = true;
    filesRead = false; // 목록이 바뀌었으니 다시 읽을 수 있다
    renderFiles();
    return void ($("file-list").querySelectorAll("button")[Math.min(i, FILES.length - 1)] || $("drop")).focus();
  }
  if (el.dataset.asset) return void openAsset(Number(el.dataset.asset));
  if (el.dataset.caseClear) { // 비운 뒤 그 줄의 넣을 값 칸으로
    const inputs = caseCells(el.parentElement);
    inputs.forEach((x) => { if (x.type === "checkbox") x.checked = false; else x.value = ""; });
    showCall(inputs[0]);
    syncForm();
    markTableDiff();
    return void inputs[0].focus();
  }
  const actions = {
    "start": startMode, "submit": submitCode, "run": () => judgeCode(true), "run-own-go": () => judgeCode(true, $("run-input").value),
    "solo-hint": () => loadHints(false), "solo-open": () => loadSolution(false), "solo-force": () => { S.solo.ask = true; render(); $("solo-force-no").focus(); },
    "solo-force-no": () => { S.solo.ask = false; render(); }, "solo-force-yes": () => loadSolution(true),
    "result-tutor-hint": tutorHint,
    "result-hint": () => { S.soloOpen = "hint"; setMode("solo"); if (!S.solo.shown.length) loadHints(false); }, // 결과의 힌트는 처음부터 푸는 힌트(오른쪽 칸에 열린다)
    "result-learn": async () => { if (!S.solo.sol) await loadSolution(false); S.soloOpen = "sol"; setMode("solo"); $("solo-box").scrollTop = 0; },
    "way-change": () => { S.choosing = !S.choosing && !!S.mode; render(); (S.choosing ? document.querySelector("[data-way]") : $("way-change")).focus(); },
    "solo-fold": () => { S.soloOpen = null; render(); $("rail-hint").focus(); },
    "to-explain": () => setMode("explain"),
    "compose-run": composeRun,
    "panes-reset": paneReset,
    "problem-peek": () => { const open = $("panes").classList.toggle("peek"); el.setAttribute("aria-expanded", String(open)); el.textContent = open ? "문제 접기" : "문제 펼치기"; },
    "lang-yes": () => changeLanguage(S.langWant), "lang-no": () => { S.langWant = null; render(); $("p-lang-select").focus(); }, "debug-start": debugStart, "to-feedback": askFeedback, "fb-again": askFeedback, "fb-get": askFeedback,
    "old-feedback": () => { location.hash = `#/p/${S.pid}/feedback`; },
    "goto-line": gotoLine,
    "prep-again": prepAgain, "prep-again-top": prepAgain,
    "cp-save": saveCheckpoint, "cp-restore": () => askCode("restore"), "code-clear": () => askCode("clear"),
    "code-yes": async () => {
      const run = S.codeAsk === "pull" && S.pullThenRun;
      S.pullThenRun = false;
      await ({ restore: restoreCheckpoint, pull: pullBlocks }[S.codeAsk] || clearCode)();
      if (run) { S.codeTab = "direct"; judgeCode(true); } // 모아서 실행에서 물었다
    },
    "code-no": () => { const was = S.codeAsk; S.codeAsk = S.pullThenRun = null; render(); (was === "pull" ? $("pull-blocks").hidden ? $("compose-run") : $("pull-blocks") : $("more").querySelector("summary")).focus(); },
    "pull-blocks": () => { // 덧붙이지 않고 바꾼다. 코드 전체에 시작 코드 말고 적은 것이 있으면 먼저 묻는다
      if (warnGaps()) return;
      if (!Object.values(S.blockCode).some((b) => (b.code || "").trim())) { S.codeNote = "블록 칸에 적은 코드가 아직 없어요"; return render(); }
      return codeEmpty() ? pullBlocks() : askCode("pull");
    },
    "fq-close": () => { S.quote = null; render(); $("say").focus(); },
    "debug-close": () => { S.debug.open = false; render(); },
    "problem-fold": () => {
      const folded = $("panes").classList.toggle("folded");
      el.setAttribute("aria-expanded", folded ? "false" : "true");
      el.textContent = folded ? "문제 칸 펼치기" : "문제 칸 접기";
    },
    "reset": () => { $("reset").hidden = true; $("reset-confirm").hidden = false; $("reset-no").focus(); },
    "reset-no": () => { $("reset-confirm").hidden = true; $("reset").hidden = false; $("more").querySelector("summary").focus(); },
    "reset-yes": async () => {
      const pid = S.pid;
      clearTimeout(codeTimer); clearTimeout(blocksTimer); codeTimer = blocksTimer = null;
      const r = await api("/api/reset", { id: pid });
      if (S.pid !== pid) return;
      if (!r.ok) { $("code-error").textContent = errorNote(r.error).text; return void ($("code-error").hidden = false); }
      clearProblem(pid);
      say("처음 상태로 돌렸어요.");
      await loadState();
    },
    "p-edit": () => { location.hash = `#/edit/${S.pid}`; },
    "p-delete": () => { $("p-edit").hidden = $("p-delete").hidden = true; $("del-confirm").hidden = false; $("del-no").focus(); },
    "del-no": () => { $("del-confirm").hidden = true; $("p-edit").hidden = $("p-delete").hidden = false; $("more").querySelector("summary").focus(); },
    "del-yes": async () => {
      const pid = S.pid;
      clearTimeout(codeTimer); clearTimeout(blocksTimer); codeTimer = blocksTimer = null;
      const r = await api("/api/problems/delete", { id: pid });
      if (S.pid !== pid) return;
      if (!r.ok) { $("code-error").textContent = errorNote(r.error).text; return void ($("code-error").hidden = false); }
      S.pid = S.problem = null; // 지운 문제의 코드를 저장하러 가지 않게
      sayNext("문제를 지웠어요.");
      location.hash = "#/list";
    },
    "edit-yes": () => registerProblem(true), "edit-no": () => { $("edit-confirm").hidden = true; $("new-submit").focus(); },
    "new-next": nextStep, "new-back": () => setStep(WSTEP - 1),
    "tools-refresh": async () => { const r = await loadTools(true); $("tools-note").textContent = r.ok ? "언어 도구를 다시 확인했어요." : errorNote(r.error).text; }, // 창 아래로 밀리지 않게 단추 옆에
    "conn-toggle": () => toggleConn($("conn-panel").hidden), "conn-close": () => toggleConn(false), "note-conn": () => toggleConn(true),
    "chatgpt-login": chatgptLogin,
    "upd-open": openUpdate, "upd-close": closeUpdate, "upd-get": () => updAct("download"), "upd-reveal": () => updAct("reveal"),
    "upd-skip": async () => { const r = await updAct("skip"); if (r.ok) { closeUpdate(); say(`이 버전(${UPD.latest.version})은 건너뛰어요. ‘연결’ → ‘더 정하기’ → ‘지금 확인’에서 다시 볼 수 있어요.`); } },
    "upd-install": () => { flushSaves(); return updAct("install"); }, // 쓰던 코드를 먼저 저장한다(앱은 잠시 뒤에 끝난다)
    "upd-check": async () => {
      $("upd-note").textContent = "확인하는 중…";
      const r = await updAct("check");
      if (!r.ok) return void ($("upd-note").textContent = errorNote(r.error).text);
      $("upd-note").textContent = r.data.latest ? "" : r.data.state === "latest" ? "최신 버전이에요." : r.data.message;
      if (r.data.latest) { toggleConn(false); openUpdate(); }
    },
    "key-reveal": () => { setKeyShown($("key-value").type === "password"); $("key-value").focus(); },
    "key-save": () => saveKey(false), "key-retry": () => saveKey(false), "key-force": () => saveKey(true),
    "key-recheck-claude": () => recheckKey("claude"), "key-recheck-openai": () => recheckKey("openai"),
    "key-del-claude": () => askKeyDelete("claude"), "key-del-openai": () => askKeyDelete("openai"),
    "key-delete-no": () => { const name = keyDeleting; keyDeleting = null; renderKeyDelete(); const back = name && $(`key-del-${name}`); if (back) back.focus(); }, "key-delete-yes": deleteKey,
    "models-open": () => { toggleConn(false); openModels(); }, "models-close": () => { $("models").close ? $("models").close() : $("models").removeAttribute("open"); $("conn-toggle").focus(); },
    "tour-open": openTour, "tour-skip": () => { const last = tourAt === TOUR.length - 1; closeTour(); if (last && !CONN.ready) toggleConn(true); }, "tour-prev": () => tourStep(-1), "tour-next": () => tourStep(1),
    "drop": () => $("new-files").click(), "read-files": readFiles, "asset-close": closeAsset,
    "case-add": () => { addCaseRow(); $("case-rows").lastElementChild.querySelector("input").focus(); },
    "mode-switch": async () => {
      $("new-mode").value = $("new-mode").value === "program" ? "function" : "program"; setCaseMode(); say(`푸는 방식을 바꿨어요: ${$("new-mode").value === "program" ? "표준 입출력" : "함수(solution)"}`); $("new-mode").focus();
      if (!formCases().some((x) => x.input.trim() || x.expected.trim())) await fillCases(true, true); // 찾아 둔 예시를 바로 채운다(비어 있을 때만. 적은 케이스는 덮지 않는다)
    },
    "new-clear": () => { $("new-clear").hidden = true; $("new-clear-confirm").hidden = false; $("new-clear-no").focus(); },
    "new-clear-no": () => { $("new-clear-confirm").hidden = true; syncForm(); $("new-clear").focus(); },
    "new-clear-yes": () => { $("new-clear-confirm").hidden = true; emptyForm(); fillLangs(); formMode(false); findTable(); setStep(1, false); say("등록 화면을 비웠어요."); $("new-text").focus(); },
    "case-fill": () => fillCases(false), "case-fill-yes": () => fillCases(true), "case-fill-no": () => { $("case-fill-confirm").hidden = true; $("case-fill").focus(); },
  };
  if (!actions[el.id]) return;
  const done = actions[el.id]();
  // 키보드로 누른 실행·제출·힌트: 다시 그리며(잠겼다 풀리며) 초점이 body로 빠지면 같은 단추로 돌려놓는다
  if (e.detail === 0 && ["run", "submit", "solo-hint"].includes(el.id)) Promise.resolve(done).then(() => { const again = $(el.id); if (again && !again.disabled && again.offsetParent && document.activeElement === document.body) again.focus(); });
});

document.addEventListener("submit", (e) => {
  e.preventDefault();
  if (S.busy) return;
  ({ "composer": sendAnswer, "fq-composer": sendFollowup, "debug-composer": debugSend, "new-form": registerProblem }[e.target.id] || (() => {}))();
});

document.addEventListener("change", (e) => {
  if (e.target.id === "new-files") { addFiles(e.target.files); return void (e.target.value = ""); }
  if (e.target.id === "new-mode") return setCaseMode();
  if (e.target.id === "new-theme") return syncForm();
  if (e.target.id === "p-lang-select") return void (e.target.value !== S.problem.language && wantLanguage(e.target.value));
  if (e.target.id === "upd-auto") return void updAct("auto", { on: e.target.checked });
  if (e.target.name === "keyname") { setKeyShown(false); return renderKeyStatus(); }
  if (e.target.name === "scheme") return void chooseScheme(e.target.value);
  if (e.target.name === "client") accounts("/api/client", { client: e.target.value }, e.target.value === "cli" ? "이 PC의 Claude Code로 튜터를 불러요." : "연결한 AI로 튜터를 불러요.");
});

document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.id === "code") return codeChanged();
  if (el.id === "key-value") return renderKeyStatus(); // 글자를 고치면 앞의 결과 대신 꼴을 바로 본다
  if (el.closest("#new-form")) { syncForm(); if (el.getAttribute("aria-invalid")) clearError(); }
  if (el.classList.contains("case-val")) markTableDiff();
  if (el.id.startsWith("case-input-")) return showCall(el);
  if (el.id.startsWith("case-expected-") && el.tagName === "TEXTAREA") return grow(el);
  if (el.id === "new-text") return findTableSoon();
  if (el.dataset.block) {
    harvest();
    syncCheck(el); // 칸 글이 저장된 글과 달라지면 곧바로 '블록 코드 확인'(같아지면 걷는다)
    return grow(el);
  }
  if (el.matches(".composer textarea")) grow(el);
});

document.addEventListener("keydown", (e) => {
  const el = e.target;
  if (e.key === "Enter" && !e.isComposing && el.dataset && el.dataset.send && (el.tagName === "INPUT" || e.ctrlKey || e.metaKey)) { // 한 줄 칸은 Enter, 여러 줄 칸은 Ctrl/Cmd+Enter
    e.preventDefault();
    return $(el.dataset.send).click();
  }
  if (e.key === "Escape" && paneDrag) return paneEnd(e, true); // 끌던 것은 처음 너비로
  if (el.classList && el.classList.contains("sep") && paneKey(e)) return;
  if (e.key === "Escape" && $("more").open) { $("more").open = false; return $("more").querySelector("summary").focus(); }
  if (e.key === "Escape" && !$("conn-panel").hidden && !el.matches("textarea")) return toggleConn(false);
  if (el.getAttribute && el.getAttribute("role") === "tab" && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
    const tabs = [...el.parentElement.querySelectorAll("[role=tab]")];
    const next = tabs[(tabs.indexOf(el) + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    next.click();
    return next.focus();
  }
  if (el.id === "code" || (el.dataset && el.dataset.block)) codeKeys(e);
});

$("code").addEventListener("scroll", syncGutter);
$("more").addEventListener("toggle", () => { if (!$("more").open) { $("reset-confirm").hidden = true; $("reset").hidden = false; } }); // 메뉴를 닫으면 처음부터의 물음도 접는다
document.addEventListener("click", (e) => {
  const summary = e.target.closest("details.case-fold > summary");
  if (summary) S.casesOpen = !summary.parentElement.open;
  if ($("more").open && !e.target.closest("#more")) $("more").open = false;
});
window.addEventListener("hashchange", route);
window.addEventListener("pagehide", () => { leaving = true; flushSaves(); if (paneTimer) paneSave(); });
window.addEventListener("pageshow", () => { leaving = false; });

// 파일은 등록 화면 어디에 놓아도 받는다(놓친 파일을 브라우저가 열어 적던 글을 잃지 않게)
const dragFiles = (e) => S.view === "new" && [...e.dataTransfer.types].includes("Files");
document.addEventListener("dragover", (e) => { if (dragFiles(e)) { e.preventDefault(); $("drop").classList.add("over"); } });
document.addEventListener("dragleave", (e) => { if (!e.relatedTarget) $("drop").classList.remove("over"); });
document.addEventListener("drop", (e) => { if (!dragFiles(e)) return; e.preventDefault(); $("drop").classList.remove("over"); if (!S.busy) addFiles(e.dataTransfer.files); }); // 읽는 중에는 받지 않는다
$("asset").addEventListener("close", () => { $("asset-body").innerHTML = ""; }); // PDF 보기를 내린다

$("tour").addEventListener("close", () => { api("/api/tour"); stopTourDemo(); }); // 닫으면(Esc 포함) 봤다고 적는다. 다시 보려면 위의 ‘사용법’

addCaseRow();
accounts().then((r) => { // 연결 상태를 먼저 알아야 화면을 고른다(모델이 없으면 혼자 풀기)
  route();
  if (r.ok && !r.data.tour_seen) openTour(); // 처음 켰을 때만 안내를 띄운다
});
updAct("status"); // 서버가 켤 때와 24시간마다 새 버전을 본다. 화면은 그 결과만 10분마다 가져온다
setInterval(() => { if (!UPD || !UPD_BUSY.includes(UPD.state)) updAct("status"); }, 10 * 60 * 1000);
