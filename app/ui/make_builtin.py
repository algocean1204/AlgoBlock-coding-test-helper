"""기본 문제를 묶는다: ui/problems/<주제>/<단계>_<이름>/ → ui/builtin.json. 문제 폴더의 규칙은 ui/problems/README.md.

app에서:
  python3 ui/make_builtin.py build --no-model          # 검사를 통과한 문제를 묶는다. 가이드·블록은 ready.json에 있는 것만 싣는다(모델 0회). 다른 언어 풀이도 싣는다(그 언어 도구가 필요)
  python3 ui/make_builtin.py build                     # ready.json이 없거나 낡은 문제는 풀이 가이드(단서·방향·단계)와 블록·힌트를 만든다(모델을 부른다. 키가 있어야 한다)
  ALGOBLOCK_UI_CLIENT=cli python3 ui/make_builtin.py build   # 모델 대신 이 PC의 Claude Code(claude -p)를 부른다(개발용. 키를 쓰지 않는다)
  옵션: --model 모델:정도   문제 넣기 테마의 모델(예: claude/claude-opus-5-5:high)
        --redo ID …        그 문제의 가이드·블록과 언어별 줄 구간을 다시 만든다(다른 문제는 글과 정답 풀이가 그대로면 ready.json의 것을 다시 쓴다)
        --no-langs         파이썬 정답 풀이만 검사해 싣는다(기본은 다른 언어 정답 풀이(solution.java 등)도 검사해 싣는다. 그 언어의 도구가 기기에 있어야 한다.
                           이 옵션으로 묶으면 이미 실린 문제의 다른 언어 풀이가 묶음에서 빠진다)
        --only 폴더 …      그 문제만 검사하고 묶는다(예: hash/1_popular_shelf). 다른 문제의 행은 지금 묶음의 것을 그대로 둔다(문제 하나를 더할 때)
        --no-check         검사를 다시 돌리지 않고 폴더의 cases.json·lang.json(지난 검사가 얼린 것)을 믿는다(개발·시험용. 실을 때는 쓰지 않는다)
        --out 파일          다른 곳에 쓴다(기본 ui/builtin.json)
        --workers N        한 번에 몇 문제(기본 4)

문제마다
1. problemkit.check를 통과해야 싣는다(두 풀이 대조, 오답·느린 풀이가 걸리는지, 시간).
2. 가이드는 새로 풀지 않는다: solution.py가 정석 가이드 코드이고, 단서·방향·단계와 블록·힌트만 모델이 쓴다(Tutor.prepare 그대로).
   가이드가 채점을 통과하고, 블록을 이으면 가이드 코드와 같고, 모든 블록에 힌트가 3개 있어야 싣는다. 안 되면 세 번까지 다시 만든다.
3. 가이드·블록의 원본은 문제 폴더의 ready.json({"source": 글·정답 풀이의 crc, "ready": …})이다. builtin.json은 빌드 결과물일 뿐이다.
   source가 지금 글·정답 풀이와 같으면 ready.json을 그대로 싣고, 다르면 다시 만들어 ready.json을 새로 쓴다.
   ready.json이 없으면(옮기는 첫 한 번) 이전 builtin.json의 것을 ready.json으로 옮긴다.
   ready.json은 손으로 고쳐도 된다. 싣기 전에 2번과 같은 모양 검사(shape)를 하고, 걸리면 그 문제를 실패로 알리고 가이드 없이 싣는다.
4. 다른 언어의 가이드·블록(readies)은 Python 계획의 글(이름·목표·확인·힌트, 단서·방향·단계)을 그대로 쓰고 그 언어 정답 풀이의 줄 구간만 다르다.
   줄 구간은 모델에게 받아 cut_by_lines로 맞추고 ready.json의 langs에 둔다. 그 언어 코드에 없는 이름을 부르는 힌트만 다시 받는다.
   그 언어 풀이를 Python 블록의 차례대로 나눌 수 없다는 답이면 {"source", "fits": false}를 적고 그 언어는 싣지 않는다(알림만 한다).
   싣기 전에 lang_ready로 본다(출처 값, 구간이 그 언어 풀이를 빈틈·겹침 없이 덮는가, 모양 검사, 블록이 같은 일을 하는가(misfits), 힌트의 이름).
   걸리면 그 언어만 빼고 싣는다(그 언어는 열 때 만든다). 모델로 build하면 걸린 까닭을 붙여 다시 받는다.
"""

import ast
import json
import math
import os
import re
import sys
import tempfile
import zlib
from bisect import bisect_right
from collections import Counter
from itertools import accumulate
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))  # 저장소 루트: app.llm

import problemkit  # noqa: E402
from stubs import LANGUAGES, stub  # noqa: E402

from tutor.common.scope import ALGORITHMS  # noqa: E402
from tutor.common.solution import body_lines, frame_flags  # noqa: E402

OUT = HERE / "builtin.json"
ROOT = HERE / "problems"


def text_of(problem: dict, cases: list[dict]) -> str:
    """본문, 제한사항, 입출력 예 표, 입출력 예 설명을 이어 붙인 문제 글."""
    names = [param["name"] for param in problem["params"]]
    rows = ["| " + " | ".join([*names, "result"]) + " |"]
    notes = []
    for n, (example, case) in enumerate(zip(problem["examples"], cases), 1):
        rows.append("| " + " | ".join([*(json.dumps(arg, ensure_ascii=False) for arg in example["args"]), case["expected"]]) + " |")
        notes.append(f"입출력 예 #{n}\n{example['note']}")
    return "\n\n".join([problem["statement"].strip(), "제한사항\n" + "\n".join(f"- {line}" for line in problem["limits"]),
                        "입출력 예\n" + "\n".join(rows), "입출력 예 설명\n" + "\n\n".join(notes)])


def entry(folder: Path, langs: bool = True, check: bool = True) -> dict:
    """문제 하나를 싣는 모양으로(가이드·블록은 아직 없다). 검사에 걸리면 싣지 않는다."""
    found = problemkit.check(folder, langs=langs) if check else []
    if found:
        raise RuntimeError("검사에 걸렸다:\n  - " + "\n  - ".join(found))
    problem = problemkit.load(folder)
    files = problem["files"]
    cases = json.loads((Path(folder) / "cases.json").read_text(encoding="utf-8"))
    limits = problemkit.saved_limits(problem)  # 효율성 케이스의 언어별 제한(검사가 잰 것). 없으면 서버가 casegen.LIMIT을 쓴다
    solutions = {"python": files["solution.py"]}
    if langs:  # 검사한 언어만 싣는다(--no-langs면 파이썬만)
        solutions |= {language: files[f"solution.{ext}"] for language, ext in problemkit.EXT.items() if language != "python" and f"solution.{ext}" in files}
    traps = traps_of(problem, solutions)
    return {
        "id": problem["id"], "theme": problem["theme"], "level": problem["level"], "title": problem["title"], "language": "python",
        "text": text_of(problem, cases), "params": problem["params"], "returns": problem["returns"],
        "examples": [{"input": case["input"], "expected": case["expected"], "note": example["note"]} for example, case in zip(problem["examples"], cases)],
        "cases": cases, "large": files["gen.py"] if any(case["kind"] == "efficiency" for case in cases) else "", **({"limits": limits} if limits else {}),
        "signals": problem["signals"], "pattern": problem["pattern"], "learn": problem["learn"], "pitfalls": problem["pitfalls"], "ladder": problem["ladder"],
        "languages": [language for language in LANGUAGES if language in solutions], "solutions": solutions,
        "starters": {language: stub(problem, language) for language in LANGUAGES}, **({"traps": traps} if traps else {}),
        "source": zlib.crc32((problem["statement"] + json.dumps(problem["limits"], ensure_ascii=False) + files["solution.py"]).encode()),  # 글·정답 풀이가 바뀌었는지
    }


def traps_of(problem: dict, solutions: dict) -> dict:
    """싣는 언어의 증명된 함정: {언어: [{id, what, fix, code, right, shape(있으면), at(구절 목록, 있으면), fails·outs 또는 varies}]}. 글은 함정 목록에서, 증명은 lang.json(검사가 얼린 것)에서 온다.
    varies: 결과가 정해지지 않은 동작이라 떨어지는 케이스가 기기마다 다를 수 있다(떨어진 케이스 목록을 싣지 않는다). outs: 틀린 답을 낸 케이스의 돌려준 값(짧게, 길면 지문).
    code·right: 사용자 코드가 그 함정의 꼴인지 보는 이름(튜터가 후보를 거른다). 증명 검사와 같게 흔한 낱말과 한 글자는 뺀다.
    right_base: 그 언어 정답 풀이(주석 밖)에 right 이름이 나오는 횟수의 합. code가 없는 함정은 사용자 코드에서 이보다 적게 나와야 후보다."""
    from tutor.debug.rules import right_count

    path = problem["dir"] / "lang.json"
    saved = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    text = {row["id"]: row for rows in problemkit.traps().values() for row in rows}
    names = lambda row, key: [term for term in text[row["trap"]][key] if problemkit.anchor(term)]

    def one(row: dict, language: str) -> dict:
        trap = {"id": row["trap"], "what": text[row["trap"]]["what"], "fix": text[row["trap"]]["fix"], "code": names(row, "code"), "right": names(row, "right"),
                **{key: text[row["trap"]][key] for key in ("shape",) if key in text[row["trap"]]}, **{key: row[key] for key in ("at", "fails", "outs", "varies") if key in row}}
        return trap | {"right_base": right_count(trap, solutions[language])}

    return {language: [one(row, language) for row in rows if row["trap"] in text] for language, rows in saved.items() if language in solutions}


def ready_of(row: dict) -> dict:
    """풀이 가이드(단서·방향·단계)와 블록 계획을 튜터 엔진으로 만든다. 모델을 부른다."""
    from tutor import Tutor

    problem = problemkit.load(ROOT / row["theme"] / row["id"].removeprefix(row["theme"] + "_"))
    cases = problemkit.build_cases(problem)
    for case, frozen in zip(cases, row["cases"]):
        case["expected"] = frozen["expected"]

    def check(_pid, code):
        ran = problemkit.run("python", code, cases, problemkit.LIMIT["python"])
        return {"status": next((r["status"] for r in ran if r["status"] != "passed"), "passed"),
                "cases": [{"id": c["id"], "input": json.dumps(c["args"], ensure_ascii=False)[:300], "expected": c["expected"], "got": r["got"] or "", "error": r["why"], "status": r["status"]}
                          for c, r in zip(cases, ran)]}

    with tempfile.TemporaryDirectory() as folder:
        tutor = Tutor(str(Path(folder) / "tutor.db"), check=check, given=lambda _pid, _language: {"code": row["solutions"]["python"]})
        try:
            tutor.store.put_problem(row["id"], "python", row["text"], title=row["title"])
            done = tutor.prepare(row["id"])
            ctx = tutor.store.load(row["id"])
        finally:
            tutor.close()
    if done.status != 200 or ctx.solution is None or not ctx.solution.verified:
        raise RuntimeError(f"검증된 풀이 가이드를 만들지 못했다 {done.status} {str(done.body)[:300]}")
    ready = {"fact": {"spec": ctx.spec, "patterns": ctx.patterns, "skills": ctx.skills, "size": ctx.size}, "solution": asdict(ctx.solution), "plan": asdict(ctx.plan)}
    shape(ready, row["solutions"]["python"])
    return ready


def shape(ready: dict, code: str, language: str = "python") -> None:
    """실을 수 있는 가이드·블록인지 본다(모델이 만든 것과 손으로 고친 ready.json 둘 다). code는 그 언어의 정답 풀이. 걸리면 RuntimeError."""
    solution, blocks = ready["solution"], ready["plan"]["blocks"]
    if "\n".join(block["reference"] for block in blocks) != solution["code"]:
        raise RuntimeError("블록을 이은 것이 가이드 코드와 다르다")
    if solution["code"].rstrip("\n") != code.rstrip("\n"):
        raise RuntimeError("가이드 코드가 정답 풀이와 다르다")
    if any(len(block["hints"]) < 3 or not all(block["hints"]) or not block["name"] or not block["goal"] for block in blocks):
        raise RuntimeError("힌트가 3개보다 적거나, 빈 힌트·이름·목표가 있는 블록이 있다")
    empty = [block["id"] for block in blocks if not body_lines(block["reference"], language)]
    if empty:
        raise RuntimeError(f"틀 줄·빈 줄·주석만 있는 블록이 있다: {', '.join(empty)}")
    if not solution["clues"] or not solution["verified"]:
        raise RuntimeError("단서가 없거나 검증되지 않은 가이드다")
    start = 1
    for block in blocks:  # lines는 1부터 빈틈·겹침 없이 reference의 줄을 그대로 덮는다
        size = block["reference"].count("\n") + 1
        if block.get("lines") and list(block["lines"]) != [start, start + size - 1]:
            raise RuntimeError(f"블록 {block.get('id')}의 lines {block['lines']}가 코드 줄({start}~{start + size - 1})과 다르다")
        start += size


def lang_source(row: dict, language: str) -> int:
    """그 언어의 줄 구간이 기대는 것(Python 계획의 블록 구간과 그 언어 정답 풀이)의 crc. 다르면 줄 구간을 다시 받는다."""
    return zlib.crc32(json.dumps([[block["reference"] for block in row["ready"]["plan"]["blocks"]], row["solutions"][language]], ensure_ascii=False).encode())


def stray_names(hint: str, row: dict, language: str) -> list[str]:
    """힌트가 부르는 코드 이름 가운데 그 언어 정답 풀이에 없는 것(다른 언어 풀이에만 있고 문제 글에도 없는 이름)."""
    from tutor.common.talk_rules import code_names

    return sorted(set(code_names(hint, "\n".join(row["solutions"].values()), row["text"])) - set(code_names(hint, row["solutions"][language], "")))


def lang_ready(row: dict, language: str, saved: dict) -> dict:
    """Python 계획(row["ready"])의 글에 그 언어 정답 풀이의 줄 구간을 입힌 가이드·블록. 걸리면 RuntimeError.
    saved = ready.json의 langs[언어]: {"source": lang_source, "lines": 블록마다 [처음, 끝],
    "hints": {블록 id: [다시 받은 힌트, 그대로 쓰는 자리는 빈 글]}(그 언어 코드에 없는 이름을 부른 힌트가 있을 때만)}."""
    from tutor.plan.nodes import cut_by_lines
    from tutor.state import Block

    ready, code = row["ready"], row["solutions"][language].strip("\n")
    blocks, spans = ready["plan"]["blocks"], [list(span) for span in saved.get("lines") or []]
    if saved.get("source") != lang_source(row, language):
        raise RuntimeError("출처 값이 지금 Python 계획의 블록 구간·그 언어 정답 풀이와 다르다")
    cut = cut_by_lines([Block(block["id"], block["kind"], block["name"], block["goal"], lines=span) for block, span in zip(blocks, spans)], code, language) \
        if len(spans) == len(blocks) else None
    if cut is None or [block.lines for block in cut] != spans:
        raise RuntimeError(f"줄 구간 {spans}이 블록마다 하나씩 그 언어 정답 풀이를 1번 줄부터 끝까지 빈틈·겹침 없이 나누지 않는다")
    mine = saved.get("hints") or {}

    def hint(block: dict, n: int, text: str) -> str:  # Python 힌트가 그 언어 코드에 없는 이름을 부를 때만 다시 받은 것을 쓴다
        again = (mine.get(block["id"]) or [])[n:n + 1]
        return again[0] if stray_names(text, row, language) and again and again[0] else text

    out = {**ready, "solution": {**ready["solution"], "code": code},
           "plan": {**ready["plan"], "blocks": [{**block, "reference": got.reference, "lines": got.lines, "hints": [hint(block, n, text) for n, text in enumerate(block["hints"])]}
                                                for block, got in zip(blocks, cut)]}}
    shape(out, code, language)
    found = misfits(ready["plan"]["blocks"], out["plan"]["blocks"], language)
    if found:
        raise RuntimeError("블록이 Python 블록과 같은 일을 하지 않는다: " + "; ".join(found))
    found = [f"{block['id']} 힌트가 그 언어 코드에 없는 이름 {stray_names(text, row, language)}을 부른다" for block in out["plan"]["blocks"] for text in block["hints"]
             if stray_names(text, row, language)] + problemkit.ready_bound(out)
    if found:
        raise RuntimeError("; ".join(found))
    return out


_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")
_QUOTED = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'")
_KEYWORDS = frozenset("if for while return else elif in of not and or def fn function let mut const var new int long short double float bool boolean char "
                      "string str void auto true false none null public private static final class i32 i64 u8 u32 u64 usize isize vec std as pub use "
                      "import using include namespace break continue self this do switch case match loop".split())
# 일을 하지 않는 줄: 함수 머리(def·fn·function·Java·C++의 메서드·함수 머리), 값 없는 필드 선언(private int n; static vector<int> memo;), 맨 앞에서 시작하는 값 없는 전역 선언(int n, m;)
_HEAD = re.compile(r"^(?:def|function)\s+\w+|^(?:(?:pub|async)\s+)*fn\s+\w+|^(?!(?:if|for|while|switch|else|catch|do|return|new|throw)\b)"
                   r"(?:(?:public|private|protected|static|final|inline|const|virtual)\s+)*[\w:<>\[\],&*\s]+?\s+[\w:]+\s*\([^;]*\)\s*(?:const\s*)?(?:throws\s+[\w.,\s]+)?\{$")
_DECL = re.compile(r"^(?:(?:public|private|protected|static|final)\s+)+[\w<>\[\],\s]+\s+\w+\s*;$")
_GLOBAL = re.compile(r"^[A-Za-z_][\w:<>,\s&*]*\s+\w+(?:\s*,\s*\w+)*(?:\[\w*\])*\s*;\s*(?://.*)?$")


def _words(text: str, language: str) -> set:
    """글자 상수와 주석을 뺀 이름·수(밑줄을 빼고 소문자로: root_a와 rootA는 같다)."""
    text = re.sub(r"#.*$" if language == "python" else r"//.*$", "", _QUOTED.sub(" ", text), flags=re.M)
    return {word.replace("_", "").lower() for word in _WORD.findall(text)}


def _works(reference: str, language: str) -> bool:
    """틀 줄·빈 줄·주석과 일을 하지 않는 줄(_HEAD, _DECL, _GLOBAL)을 빼고 남는 줄이 있는가."""
    rows = reference.splitlines()
    bare = [re.sub(r"#.*$" if language == "python" else r"//.*$", "", row).rstrip() for row in rows]
    return any(not skip and _words(row, language) - _KEYWORDS and not _HEAD.match(row.strip()) and not _DECL.match(row.strip())
               and not (language != "python" and _GLOBAL.match(row)) for row, skip in zip(bare, frame_flags(rows, language, False)))


def _aligned(score: list[list[float]], floor: float) -> dict:
    """두 풀이의 줄을 차례를 지키며 맞춘다(점수 합이 가장 큰 짝). {Python 줄: 그 언어 줄}."""
    rows, cols = len(score), len(score[0]) if score else 0
    best = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(rows):
        for j in range(cols):
            best[i + 1][j + 1] = max(best[i][j + 1], best[i + 1][j], best[i][j] + score[i][j] if score[i][j] >= floor else 0.0)
    pairs, i, j = {}, rows, cols
    while i and j:
        if score[i - 1][j - 1] >= floor and best[i][j] == best[i - 1][j - 1] + score[i - 1][j - 1]:
            pairs[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif best[i][j] == best[i - 1][j]:
            i -= 1
        else:
            j -= 1
    return pairs


_DEFINED = re.compile(r"(\w+)\s*(?:[-+*/%|&^]|<<|>>)?=(?!=)|\b([A-Za-z_][\w:]*)(?:<[^;()]*>)?(?:\[\])*\s+(\w+)\s*[(;\[{]")  # 대입·선언·함수 머리가 만드는 이름


def _made(reference: str, language: str, function: bool) -> set:
    """그 언어 블록이 만드는 이름(function이면 함수 이름만)."""
    out = set()
    for line in reference.splitlines():
        line = re.sub(r"//.*$", "", _QUOTED.sub(" ", line))
        if function:
            out |= {found.group(1) for found in [re.search(r"(\w+)\s*\(", line)] if found and _HEAD.match(line.strip())}
        else:
            out |= {a or b for a, kind, b in _DEFINED.findall(line) if a or kind.lower() not in _KEYWORDS | {"new", "throw", "case"}}
    return {name.replace("_", "").lower() for name in out} - _KEYWORDS


def _handoffs(python: list[dict]) -> list[tuple]:
    """Python 블록이 만들어(대입·함수 정의) 뒤 블록에 넘기는 이름: [(블록 번호, 이름, 만든 줄, 함수인가)].
    반복 변수와 글자 그대로의 값을 붙인 이름(LIMIT = 24, INF = float("inf"))은 뺀다: 다른 언어에서는 흔히 이름 없이 그 자리에 쓴다."""
    starts = list(accumulate([0] + [block["reference"].count("\n") + 1 for block in python]))
    at = lambda line: bisect_right(starts, line - 1) - 1  # noqa: E731
    source = "\n".join(block["reference"] for block in python)
    made, used, skip = {}, {}, set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.For, ast.comprehension)):
            skip |= {name.id for name in ast.walk(node.target) if isinstance(name, ast.Name)}
        if isinstance(node, ast.Assign) and (isinstance(node.value, ast.Constant) or isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                                             and not node.value.keywords and all(isinstance(arg, ast.Constant) for arg in node.value.args)):
            skip |= {target.id for target in node.targets if isinstance(target, ast.Name)}
        if isinstance(node, ast.Name):
            (made if isinstance(node.ctx, ast.Store) else used).setdefault(node.id, []).append((node.lineno, False))
        elif isinstance(node, ast.FunctionDef):
            made.setdefault(node.name, []).append((node.lineno, True))
    rows = source.splitlines()
    return [(at(line), name, rows[line - 1], function) for name, places in made.items() if name not in skip
            for line, function in [min(places)] if any(at(later) > at(line) for later, _ in used.get(name, []))]


def misfits(python: list[dict], blocks: list[dict], language: str) -> list[str]:
    """그 언어 블록이 같은 자리의 Python 블록과 같은 일을 하는지 이름과 줄로 견준다(모델 없음). 어긋난 블록마다 까닭 한 줄(비면 통과).
    1. Python 블록에는 일을 하는 줄이 있는데 이 블록에는 함수 머리·값 없는 선언·틀 줄뿐이다.
    2. Python 블록이 쓰는 이름(변수·함수 이름. 여러 블록에 나오는 이름은 가볍게 센다)이 대부분 다른 블록에 있고, 이 블록의 이름도 다른 Python 블록의 것이다.
    3. Python 블록에서 그 언어 풀이에 거의 그대로 있는 줄 가운데 이 블록에 오는 것(차례대로 맞춘 짝이나 가장 닮은 줄이 이 블록에 있다)이 절반이 안 되고,
       나머지가 다른 블록의 서로 다른 줄 둘 이상과 닮았다.
    4. Python 블록이 만들어 뒤 블록에 넘기는 이름(방향 표, 비교 함수, 정렬한 값)이 그 언어 풀이 어디에도 없고, 이 블록에 그 줄과 닮은 줄도,
       이름만 바꿔 만든 것(같은 자리에서 새로 만드는 이름. 함수면 함수)도 없다: 그 단계가 그 언어에는 없거나 다른 블록과 합쳐졌다.
    같은 일을 다른 꼴로 쓴 줄(세 줄 if를 한 줄 삼항식으로)은 걸리지 않게 이름이 엇갈리거나 닮은 줄이 다른 블록에 있을 때만 본다."""
    mine = [_words(block["reference"], "python") - _KEYWORDS for block in python]
    theirs = [_words(block["reference"], language) - _KEYWORDS for block in blocks]
    used = Counter(name for names in mine for name in names)
    weight = lambda names: sum(math.log(1 + len(mine) / used[name]) for name in names if used[name])  # noqa: E731 - 여러 블록에 나오는 이름은 가볍다
    lines = lambda rows, lang: [(k, words) for k, block in enumerate(rows) for line in block["reference"].splitlines() if (words := _words(line, lang) - _KEYWORDS)]  # noqa: E731
    left, right = lines(python, "python"), lines(blocks, language)
    score = [[2 * len(a & b) / (len(a) + len(b)) for _, b in right] for _, a in left]
    pairs = _aligned(score, 0.4)
    everywhere, words = set().union(*theirs), set().union(*mine)
    near = lambda a, b: a == b or min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a))  # noqa: E731 - sorted와 sort
    alike = lambda a, b: 2 * sum(any(near(x, y) for y in b) for x in a) / (len(a) + len(b)) if a and b else 0  # noqa: E731
    handoffs = _handoffs(python)
    found = []
    for k, (block, mirror) in enumerate(zip(python, blocks)):
        label = f"{mirror['id']}({mirror['name']})"
        if _works(block["reference"], "python") and not _works(mirror["reference"], language):
            found.append(f"{label}에 함수 머리·선언·틀 줄만 있고 이 블록의 일을 하는 줄이 없다")
            continue
        own = mine[k] & set().union(*theirs)
        there = [weight(own & names) / weight(own) for names in theirs] if weight(own) else []
        back = [weight(theirs[k] & names) / weight(theirs[k]) for names in mine] if weight(theirs[k]) else []
        if there and back and there[k] < max(there) / 2 and back[k] < max(back) / 2:
            found.append(f"{label}: 이 블록의 일에 쓰는 이름은 {blocks[there.index(max(there))]['id']}에 있고, 이 블록의 코드는 Python {python[back.index(max(back))]['id']}의 일이다")
            continue
        close = [i for i, (at, _) in enumerate(left) if at == k and max(score[i], default=0) >= 0.6]
        home = [i for i in close if i in pairs and right[pairs[i]][0] == k or any(right[j][0] == k and score[i][j] >= max(score[i]) for j in range(len(right)))]
        away = {score[i].index(max(score[i])) for i in close if i not in home}
        if len(away) >= 2 and len(home) * 2 < len(close):
            elsewhere = Counter(right[j][0] for j in away).most_common(1)[0][0]
            found.append(f"{label}: 이 블록의 일을 하는 줄이 {blocks[elsewhere]['id']}에 있다")
            continue
        for _, name, row, function in [handoff for handoff in handoffs if handoff[0] == k]:
            key = name.replace("_", "").lower()
            look = _words(row, "python") - _KEYWORDS - {key}
            if key not in everywhere and not any(alike(look, _words(line, language) - _KEYWORDS) >= 0.5 for line in mirror["reference"].splitlines()) \
                    and not _made(mirror["reference"], language, function) - words:
                found.append(f"{label}: Python 블록이 만들어 뒤 블록에 넘기는 {name}이(가) 이 언어 풀이에 없다(이 단계가 이 언어에는 없거나 다른 블록과 합쳐졌다)")
                break
    return found


@dataclass
class Span:
    id: str
    lines: list[int]


@dataclass
class Spans:
    """그 언어 풀이에서 블록마다 맡을 줄 구간(모델 출력). fits: 그 언어 풀이를 같은 블록으로 같은 차례에 나눌 수 있는가"""

    blocks: list[Span]
    fits: bool = True


def span_messages(row: dict, language: str, code: str, before: str = "") -> list[dict]:
    """before: 앞 답과 그 답을 쓸 수 없었던 까닭(다시 받을 때)."""
    from tutor.debug.rules import numbered

    lines = [f"같은 풀이를 Python과 {language}로 썼다. Python 풀이는 아래 블록으로 나뉘어 있다(차례대로. 코드는 그 블록이 맡은 Python 줄이다).",
             *[f"- {block['id']} {block['name']}: {block['goal']}\n{block['reference']}" for block in row["ready"]["plan"]["blocks"]], "",
             f"{language} 풀이(줄 번호 붙임):\n{numbered(code)}", "",
             f"{language} 풀이를 같은 블록으로 나눈다. 블록의 수·id·차례는 그대로다. 블록마다 그 블록의 일을 하는 {language} 줄을 lines에 [처음 줄 번호, 끝 줄 번호]로 적는다.",
             "첫 블록은 1번 줄에서 시작하고, 다음 블록은 앞 블록의 끝 줄 바로 다음 줄에서 시작하고, 마지막 블록은 마지막 줄에서 끝난다. import·클래스와 함수의 머리·닫는 괄호·빈 줄도 앞이나 뒤 블록에 넣는다.",
             "블록마다 그 블록의 목표를 하는 줄이 그 블록 안에 있어야 한다. 함수 머리·값 없는 선언 한 줄, 틀 줄·빈 줄·주석은 일을 하는 줄이 아니다. "
             "다른 블록의 일을 하는 줄을 이 블록에 넣지 않는다.",
             f"어떤 블록의 일을 하는 줄이 {language} 풀이에 같은 차례로 이어져 있지 않으면(도움 함수가 다른 자리에 있다, 다른 블록 안에 섞여 있다, 그 일을 하는 줄이 따로 없다) "
             "다른 블록의 줄을 옮겨 채우지 말고 fits를 false로, blocks를 빈 목록으로 한다.",
             'JSON {"fits": true 또는 false, "blocks": [{"id", "lines": [처음, 끝]}]}']
    if before:
        lines += ["", f"앞 답은 쓸 수 없었다: {before}"]
    return [{"role": "system", "content": "너는 코딩테스트 튜터의 블록 설계자다. 블록으로 나눈 풀이를 다른 언어로 쓴 코드에서 블록마다 맡을 줄을 찾는다."},
            {"role": "user", "content": "\n".join(lines)}]


def lang_plan(row: dict, language: str, before: str = "") -> dict:
    """ready.json의 langs[언어]를 만든다: 줄 구간을 모델에게 받아 cut_by_lines로 맞추고(작은 어긋남은 고친다), 그 언어 코드에 없는 이름을 부르는 힌트만 다시 받는다.
    블록의 글은 Python 계획 그대로다. lang_ready의 검사를 통과한 것만 돌려준다. 다시 받을 때는 앞 답과 그 답을 쓸 수 없었던 까닭을 함께 보낸다.
    그 언어 풀이를 같은 블록·같은 차례로 나눌 수 없다는 답(fits false)이면 {"source", "fits": False}를 돌려준다(그 언어는 싣지 않는다).
    before: 이미 있던 구간을 쓸 수 없었던 까닭(첫 요청부터 붙인다). 세 번까지 해 보고 안 되면 RuntimeError. 모델을 부른다."""
    from tutor.common.talk_rules import hint_problems, repeated_hints
    from tutor.llm import LlmError, llm, model_name
    from tutor.plan.nodes import cut_by_lines
    from tutor.plan.prompts import hint_messages
    from tutor.state import Block, MendedHints

    code = row["solutions"][language].strip("\n")
    blocks = [Block(block["id"], block["kind"], block["name"], block["goal"], checks=block["checks"], hints=block["hints"]) for block in row["ready"]["plan"]["blocks"]]
    why = ""
    for _ in range(3):  # 모델 답이 흔들려 한 번 안 되는 일이 있다
        try:
            answer = llm(model_name()).use(span_messages(row, language, code, before), Spans, task="plan.draft_blocks")
            if not answer.fits:
                return {"source": lang_source(row, language), "fits": False}
            got = {span.id: span.lines for span in answer.blocks}
            before = f"{json.dumps([[block.id, got.get(block.id)] for block in blocks])}. "
            cut = cut_by_lines([replace(block, lines=list(got.get(block.id) or [])) for block in blocks], code, language)
            if cut is None:
                raise RuntimeError(f"줄 구간을 쓸 수 없다: {[got.get(block.id) for block in blocks]}")
            empty = [block.id for block in cut if not body_lines(block.reference, language)]
            if empty:  # 힌트를 다시 받기 전에 본다(lang_ready의 모양 검사와 같은 것)
                raise RuntimeError(f"틀 줄·빈 줄·주석만 있는 블록이 있다: {', '.join(empty)}")
            found = misfits(row["ready"]["plan"]["blocks"], [asdict(block) for block in cut], language)
            if found:
                raise RuntimeError("블록이 Python 블록과 같은 일을 하지 않는다: " + "; ".join(found))
            saved = {"source": lang_source(row, language), "lines": [block.lines for block in cut]}
            bad = {block.id: [n for n, text in enumerate(block.hints) if stray_names(text, row, language)] for block in cut}
            bad = {key: rows for key, rows in bad.items() if rows}
            if bad:
                said = {block.id: [f"{language} 코드에 없는 이름 {', '.join(stray_names(block.hints[n], row, language))}을 부른 {n + 1}번 질문" for n in bad[block.id]]
                        for block in cut if block.id in bad}
                new = {item.id: item.hints for item in llm(model_name()).use(hint_messages({"ctx": SimpleNamespace(problem_text=row["text"])}, cut, said), MendedHints, task="plan.hints").blocks}
                saved["hints"] = {}
                for at, block in enumerate(cut):
                    if block.id not in bad:
                        continue
                    again = ["" for _ in block.hints]
                    for n in bad[block.id]:
                        again[n] = ((new.get(block.id) or [])[n:n + 1] or [""])[0].strip()
                    merged = [again[n] or text for n, text in enumerate(block.hints)]
                    if not all(again[n] and not hint_problems(again[n], problem=row["text"], reference=block.reference, later_names=[b.name for b in cut[at + 1:]], clue=n == 1, code=code)
                               for n in bad[block.id]) or repeated_hints(merged):
                        raise RuntimeError(f"{block.id}의 다시 받은 힌트가 원칙을 어겼다: {[again[n] for n in bad[block.id]]}")
                    saved["hints"][block.id] = again
            lang_ready(row, language, saved)
            return saved
        except (LlmError, RuntimeError) as exc:
            why = f"{type(exc).__name__}: {str(exc)[:400]}"
            before = (before + str(exc)[:400]) if isinstance(exc, RuntimeError) else ""
    raise RuntimeError(f"{language}의 줄 구간을 만들지 못했다: {why}")


def build(args: list[str]) -> int:
    def value(name: str, default: str) -> str:
        return args[args.index(name) + 1] if name in args else default

    redo = set()
    for word in args[args.index("--redo") + 1:] if "--redo" in args else []:
        if word.startswith("--"):
            break
        redo.add(word)
    if "--model" in args:
        os.environ["ALGOBLOCK_THEME_INGEST"] = value("--model", "")
    out = Path(value("--out", str(OUT)))
    old = {row["id"]: row for row in (json.loads(out.read_text(encoding="utf-8")) if out.exists() else []) if "source" in row}
    only = []
    for word in args[args.index("--only") + 1:] if "--only" in args else []:
        if word.startswith("--"):
            break
        only.append(word.strip("/").removeprefix("problems/"))
    folders = sorted(path.parent for path in ROOT.rglob("problem.json") if "--no-check" not in args or (path.parent / "cases.json").is_file())
    if "--only" in args:
        names = {f"{folder.parent.name}/{folder.name}" for folder in folders}
        if not only or set(only) - names:
            print(f"--only에는 문제 폴더를 <주제>/<단계>_<이름>으로 적는다. 찾지 못한 것: {sorted(set(only) - names) or '(없음)'}", file=sys.stderr)
            return 2
        folders = [folder for folder in folders if f"{folder.parent.name}/{folder.name}" in only]

    def one(folder: Path):
        name = f"{folder.parent.name}/{folder.name}"
        try:
            row = entry(folder, "--no-langs" not in args, "--no-check" not in args)
        except Exception as exc:  # noqa: BLE001 - 하나가 안 돼도 나머지는 묶는다
            return name, None, f"{type(exc).__name__}: {str(exc)[:1500]}"
        before, path = old.get(row["id"]) or {}, folder / "ready.json"
        langs = {}  # ready.json의 langs: 언어마다 줄 구간(lang_ready)

        def keep(ready: dict) -> None:
            path.write_text(json.dumps({"source": row["source"], "ready": ready, **({"langs": langs} if langs else {})}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        if not path.exists() and before.get("ready") and before.get("source") == row["source"] and row["id"] not in redo:
            keep(before["ready"])  # 옮기는 첫 한 번: 이전 builtin.json의 가이드·블록을 ready.json으로 옮긴다
        try:
            kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() and row["id"] not in redo else {}
            langs.update(kept.get("langs") or {})
            if kept.get("source") == row["source"]:
                shape(kept["ready"], row["solutions"]["python"])  # 손으로 고친 것이 구조를 깨지 않았는지
        except Exception as exc:  # noqa: BLE001
            return name, row, f"ready.json이 틀렸다(가이드 없이 싣는다): {type(exc).__name__}: {str(exc)[:600]}"
        if kept.get("source") == row["source"]:
            row["ready"] = kept["ready"]  # 글과 정답 풀이가 그대로다: 만들어 둔 가이드·블록을 다시 쓴다
        elif "--no-model" not in args:
            why = ""
            for _ in range(3):  # 모델 답이 흔들려 한 번 안 되는 일이 있다: 세 번까지 만든다
                try:
                    row["ready"] = ready_of(row)
                    keep(row["ready"])
                    break
                except Exception as exc:  # noqa: BLE001
                    why = f"{type(exc).__name__}: {str(exc)[:600]}"
            else:
                return name, row, f"가이드·블록을 만들지 못했다(가이드 없이 싣는다): {why}"
        elif not path.exists():  # 키 없이 넣은 새 문제: 가이드 없이 싣는 것이 정상이다(알리기만 하고 실패로 세지 않는다)
            print(f"알림 {name}: ready.json이 없어 가이드 없이 싣는다(키를 넣고 모델로 build하면 만든다)", file=sys.stderr)
        else:  # 있던 가이드가 낡았거나 다시 만들라고 골랐다: 조용히 빠지면 안 된다
            have = f"ready.json의 출처 값 {kept['source']}이(가) 지금 글·정답 풀이의 값 {row['source']}과 다르다" if kept.get("source") is not None else "--redo로 다시 만들라고 골랐다"
            return name, row, f"가이드 없이 싣는다: {have}. 모델 없이는 다시 만들 수 없다(모델로 build하거나, 가이드와 상관없는 수정이면 출처 값을 맞춘다)"
        failed = []
        for language in [language for language in row["solutions"] if language != "python"] if row.get("ready") else []:  # 다른 언어의 가이드·블록
            saved, why = langs.get(language) or {}, ""
            if saved.get("source") == lang_source(row, language):
                if saved.get("fits") is False:  # 그 언어 풀이를 Python 블록의 차례대로 나눌 수 없다: 열 때 만드는 길로 둔다
                    print(f"알림 {name}: {language} 풀이를 Python 블록과 같은 차례·같은 일로 나눌 수 없어 그 언어의 가이드·블록 없이 싣는다(그 언어는 처음 시작할 때 만든다)", file=sys.stderr)
                    continue
                try:
                    row.setdefault("readies", {})[language] = lang_ready(row, language, saved)
                    continue
                except RuntimeError as exc:
                    why = f"{json.dumps([[block['id'], span] for block, span in zip(row['ready']['plan']['blocks'], saved.get('lines') or [])])}. {exc}"
            if "--no-model" in args:
                if why:
                    failed.append(f"{language}: ready.json의 줄 구간이 틀렸다(그 언어의 가이드·블록 없이 싣는다. 모델로 build하면 다시 받는다): {why}")
                elif saved:
                    failed.append(f"{language}: ready.json의 줄 구간이 지금 Python 계획의 블록 구간이나 그 언어 정답 풀이와 맞지 않아 그 언어의 가이드·블록 없이 싣는다(모델로 build하면 다시 받는다)")
                else:
                    print(f"알림 {name}: ready.json에 {language} 줄 구간이 없어 그 언어의 가이드·블록 없이 싣는다(모델로 build하면 만든다)", file=sys.stderr)
                continue
            try:
                langs[language] = lang_plan(row, language, why)  # 쓸 수 없던 구간이 있으면 그 까닭을 붙여 다시 받는다
            except RuntimeError as exc:
                failed.append(f"{language}: {exc}")
                continue
            keep(row["ready"])
            if langs[language].get("fits") is False:
                print(f"알림 {name}: {language} 풀이를 Python 블록과 같은 차례·같은 일로 나눌 수 없어 그 언어의 가이드·블록 없이 싣는다(그 언어는 처음 시작할 때 만든다)", file=sys.stderr)
            else:
                row.setdefault("readies", {})[language] = lang_ready(row, language, langs[language])
        return name, row, "; ".join(failed)

    cli = os.environ.get("ALGOBLOCK_UI_CLIENT") == "cli" and "--no-model" not in args  # 개발용: 모델 대신 이 PC의 Claude Code를 부른다
    if cli:
        from tutor.eval.cli_client import ClaudeCli
        from tutor.llm import use_llm
    with use_llm(ClaudeCli()) if cli else nullcontext():
        contexts = [copy_context() for _ in folders]
        with ThreadPoolExecutor(max_workers=int(value("--workers", "4"))) as pool:
            done = list(pool.map(lambda pair: pair[0].run(one, pair[1]), zip(contexts, folders)))
    rows, bad = [], 0
    for name, row, why in done:
        if row is not None:
            rows.append(row)
        if why:
            bad += 1
            print(f"실패 {name}: {why}", file=sys.stderr)
    if only:  # 고른 문제만 새로 만들었다: 나머지 행은 지금 묶음의 것을 그대로 둔다
        wrote = {row["id"] for row in rows}
        rows += [row for row in (json.loads(out.read_text(encoding="utf-8")) if out.exists() else []) if row["id"] not in wrote]
    order = {key: n for n, key in enumerate(ALGORITHMS)}
    rows.sort(key=lambda row: (order.get(row["theme"], 99), row["level"], row["id"]))
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ready, readies = sum(bool(row.get("ready")) for row in rows), sum(len(row.get("readies") or {}) for row in rows)
    print(f"{len(rows)}개를 묶었다(이번에 검사한 문제 {len(folders)}개, 가이드·블록 {ready}개, 다른 언어의 가이드·블록 {readies}개, "
          f"언어 {sorted({language for row in rows for language in row['languages']})}) → {out}")
    return 1 if bad else 0


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "build":
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[2:]))


if __name__ == "__main__":
    main()
