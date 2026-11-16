"""기본 문제를 묶는다: ui/problems/<주제>/<단계>_<이름>/ → ui/builtin.json. 문제 폴더의 규칙은 ui/problems/README.md.

app에서:
  python3 ui/make_builtin.py build --no-model          # 검사를 통과한 문제를 묶는다. 가이드·블록은 ready.json에 있는 것만 싣는다(모델 0회). 다른 언어 풀이도 싣는다(그 언어 도구가 필요)
  python3 ui/make_builtin.py build                     # ready.json이 없거나 낡은 문제는 풀이 가이드(단서·방향·단계)와 블록·힌트를 만든다(모델을 부른다. 키가 있어야 한다)
  옵션: --model 모델:정도   문제 넣기 테마의 모델(예: claude/claude-opus-5-5:high)
        --redo ID …        그 문제의 가이드·블록을 다시 만든다(다른 문제는 글과 정답 풀이가 그대로면 ready.json의 것을 다시 쓴다)
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
"""

import json
import os
import sys
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1]))  # 저장소 루트: app.llm

import problemkit  # noqa: E402
from stubs import LANGUAGES, stub  # noqa: E402

from tutor.common.scope import ALGORITHMS  # noqa: E402

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
    """싣는 언어의 증명된 함정: {언어: [{id, what, fix, code, right, at(구절 목록, 있으면), fails 또는 varies}]}. 글은 함정 목록에서, 증명은 lang.json(검사가 얼린 것)에서 온다.
    varies: 결과가 정해지지 않은 동작이라 떨어지는 케이스가 기기마다 다를 수 있다(떨어진 케이스 목록을 싣지 않는다).
    code·right: 사용자 코드가 그 함정의 꼴인지 보는 이름(튜터가 후보를 거른다). 증명 검사와 같게 흔한 낱말과 한 글자는 뺀다.
    right_base: 그 언어 정답 풀이(주석 밖)에 right 이름이 나오는 횟수의 합. code가 없는 함정은 사용자 코드에서 이보다 적게 나와야 후보다."""
    from tutor.debug.rules import right_count

    path = problem["dir"] / "lang.json"
    saved = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    text = {row["id"]: row for rows in problemkit.traps().values() for row in rows}
    names = lambda row, key: [term for term in text[row["trap"]][key] if problemkit.anchor(term)]

    def one(row: dict, language: str) -> dict:
        trap = {"id": row["trap"], "what": text[row["trap"]]["what"], "fix": text[row["trap"]]["fix"], "code": names(row, "code"), "right": names(row, "right"),
                **{key: row[key] for key in ("at", "fails", "varies") if key in row}}
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


def shape(ready: dict, python: str) -> None:
    """실을 수 있는 가이드·블록인지 본다(모델이 만든 것과 손으로 고친 ready.json 둘 다). 걸리면 RuntimeError."""
    solution, blocks = ready["solution"], ready["plan"]["blocks"]
    if "\n".join(block["reference"] for block in blocks) != solution["code"]:
        raise RuntimeError("블록을 이은 것이 가이드 코드와 다르다")
    if solution["code"].rstrip("\n") != python.rstrip("\n"):
        raise RuntimeError("가이드 코드가 정답 풀이와 다르다")
    if any(len(block["hints"]) < 3 or not all(block["hints"]) or not block["name"] or not block["goal"] for block in blocks):
        raise RuntimeError("힌트가 3개보다 적거나, 빈 힌트·이름·목표가 있는 블록이 있다")
    if not solution["clues"] or not solution["verified"]:
        raise RuntimeError("단서가 없거나 검증되지 않은 가이드다")
    start = 1
    for block in blocks:  # lines는 1부터 빈틈·겹침 없이 reference의 줄을 그대로 덮는다
        size = block["reference"].count("\n") + 1
        if block.get("lines") and list(block["lines"]) != [start, start + size - 1]:
            raise RuntimeError(f"블록 {block.get('id')}의 lines {block['lines']}가 코드 줄({start}~{start + size - 1})과 다르다")
        start += size


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

        def keep(ready: dict) -> None:
            path.write_text(json.dumps({"source": row["source"], "ready": ready}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        if not path.exists() and before.get("ready") and before.get("source") == row["source"] and row["id"] not in redo:
            keep(before["ready"])  # 옮기는 첫 한 번: 이전 builtin.json의 가이드·블록을 ready.json으로 옮긴다
        try:
            kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() and row["id"] not in redo else {}
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
        return name, row, ""

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
    ready = sum(bool(row.get("ready")) for row in rows)
    print(f"{len(rows)}개를 묶었다(이번에 검사한 문제 {len(folders)}개, 가이드·블록 {ready}개, 언어 {sorted({language for row in rows for language in row['languages']})}) → {out}")
    return 1 if bad else 0


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "build":
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[2:]))


if __name__ == "__main__":
    main()
