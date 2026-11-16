"""기본 문제 한 개(폴더)를 읽고, 채점 케이스를 만들고, 검사한다. 모델을 부르지 않는다. 폴더 규칙은 ui/problems/README.md.

app에서:
  python3 ui/problemkit.py check ui/problems/hash/1_popular_shelf       # 파이썬 풀이만 검사
  python3 ui/problemkit.py check ui/problems/hash --langs                # 주제 폴더 전체 + 다른 언어 정답 풀이까지
  python3 ui/problemkit.py stub ui/problems/hash/1_popular_shelf java    # 그 언어의 시작 코드를 찍는다
  python3 ui/problemkit.py try ui/problems/hash/1_popular_shelf 내풀이.java  # 풀이 파일 하나를 얼린 케이스 전부에 돌려 본다(언어는 확장자로)

검사(문제마다)
1. problem.json의 모양, 형, 실전 신호가 문제 글에 그대로 있는지.
2. 케이스: 공개 예시 3개 + 정확성(gen.small, 있으면 gen.medium) + 효율성(gen.large). 인자가 선언한 형과 크기 제한에 맞는지.
3. solution.py가 모든 케이스를 제한 시간의 1/3 안에 끝내는지. 그 결과가 기대 결과다.
   효율성 케이스의 제한은 정답 풀이가 걸린 시간에서 정한다(casegen.limit_of. 효율성 케이스를 두 번 돌려 짧은 쪽).
4. brute.py(문제 글의 정의를 그대로 옮긴 풀이)가 예시·정확성 케이스와 무작위 입력 ROUNDS개에서 solution.py와 같은지.
5. wrong_*.py(흔한 오답)가 모두 걸리는지, slow_*.py(느린 풀이)가 3의 제한에서 효율성 케이스를 시간 초과하는지.
6. --langs: solution.<확장자>가 있는 언어마다 모든 케이스를 통과하고, 효율성 케이스를 그 언어 제한(3처럼 정한다)의 1/2 안에 끝내는지.
7. 언어 함정(lang_<번호>.<확장자>): 첫 줄의 id가 problems/lang_traps.json에 있고 구절이 문제 글에 있는지, 정답 풀이에서 실수 하나만 바꿨는지,
   그리고 케이스에서 실제로 떨어지는지(파이썬은 늘, 다른 언어는 --langs일 때).
통과하면 폴더에 cases.json(얼린 케이스와 기대 결과. 큰 입력은 만드는 번호만)과 limits.json(언어별 제한. 효율성 케이스가 있을 때만),
lang.json(언어 함정이 어느 케이스에서 어떤 상태로 떨어졌는지. 증명 파일이 있을 때만)을 쓴다.
"""

import functools
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import zlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from casegen import LIMIT, STEP, Rng, limit_of, seed  # noqa: E402  (LIMIT: 효율성 케이스의 언어별 제한 시간의 상한. 서버도 같은 표를 쓴다)

JUDGE_DIR = HERE.parent / "judge"
BASES = ("int", "long", "double", "bool", "string")
EXT = {"python": "py", "java": "java", "javascript": "js", "cpp": "cpp", "rust": "rs"}
ROUNDS = 300
SMALL = (12, 20)  # 정확성 케이스 수
SMALL_CHARS = 2000  # 정확성 케이스 하나의 인자 JSON 길이 상한(화면에 보여 줄 수 있는 크기)
LARGE_MAX = 3
MEDIUM_MAX = 8
LARGE_CHARS = 2_500_000
INT_MAX, LONG_MAX = 2**31 - 1, 2**53 - 1  # long도 2^53 - 1까지만: JavaScript의 수가 그 위로는 정확하지 않다
FUNCTION = "solution 함수를 완성하세요"

_judge = []
_judge_lock = threading.Lock()


def judge():
    with _judge_lock:  # 여러 스레드가 처음에 같이 부르면 올리는 중인 모듈을 다른 스레드가 본다(make_builtin --workers)
        if not _judge:
            spec = importlib.util.spec_from_file_location("algoblock_check_judge", JUDGE_DIR / "judge.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _judge.append(module)
        return _judge[0]


def parse_type(text: str) -> tuple[str, int]:
    base, dims = text.replace("[]", ""), text.count("[]")
    if base not in BASES or dims > 2 or text != base + "[]" * dims:
        raise ValueError(f"형이 아닙니다: {text}")
    return base, dims


def fits(value, typ: str) -> bool:
    base, dims = parse_type(typ)
    if dims:
        return isinstance(value, list) and all(fits(item, base + "[]" * (dims - 1)) for item in value)
    if base in ("int", "long"):
        return isinstance(value, int) and not isinstance(value, bool) and abs(value) <= (INT_MAX if base == "int" else LONG_MAX)
    if base == "double":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, bool) if base == "bool" else isinstance(value, str)


def load(folder) -> dict:
    folder = Path(folder).resolve()
    problem = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
    problem["dir"] = folder
    problem["files"] = {path.name: path.read_text(encoding="utf-8") for path in sorted(folder.iterdir()) if path.is_file() and path.suffix in (".py", ".java", ".js", ".cpp", ".rs")}
    return problem


def saved_limits(problem: dict) -> dict:
    """limits.json(지난 검사가 잰 언어별 효율성 케이스 제한, 초). 없으면 빈 것."""
    path = problem["dir"] / "limits.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def seed_of(problem: dict, salt: int = 0) -> int:
    return seed(problem["id"], salt)


def generator(problem: dict):
    scope = {"__name__": "gen"}
    exec(compile(problem["files"]["gen.py"], str(problem["dir"] / "gen.py"), "exec"), scope)  # 우리가 쓴 파일이다
    return scope


def large_args(problem: dict, index: int, gen=None) -> list:
    """효율성 케이스 하나의 인자. 채점할 때마다 같은 값이 나온다."""
    return (gen or generator(problem))["large"](Rng(seed_of(problem, 100 + index)), index)


def build_cases(problem: dict) -> list[dict]:
    """[{id, kind(example|accuracy|efficiency), args}] 기대 결과는 아직 없다."""
    gen = generator(problem)
    rows = [{"kind": "example", "args": example["args"], **({"medium": True} if example.get("big") else {})} for example in problem["examples"]]  # "big": brute·slow가 못 돌리는 예시
    rows += [{"kind": "accuracy", "args": args} for args in gen["small"](Rng(seed_of(problem, 1)))]
    if "medium" in gen:  # 정의 그대로 풀이(brute.py)로는 못 돌리는 크기의 정확성 케이스(넘침·나머지 연산 실수를 '틀림'으로 잡는다)
        rows += [{"kind": "accuracy", "args": args, "medium": True} for args in gen["medium"](Rng(seed_of(problem, 2)))]
    rows += [{"kind": "efficiency", "args": large_args(problem, index, gen), "gen": index} for index in range(int(gen.get("LARGE", 0)))]
    return [{"id": str(n), **row} for n, row in enumerate(rows, 1)]


def stable_print(folder, hash_seed: str) -> str:
    """다른 해시 씨앗의 새 프로세스에서 만든 케이스 전부의 지문. 씨앗이 달라도 같아야 한다."""
    code = ("import hashlib, json, sys; sys.path.insert(0, sys.argv[1]); import problemkit as k; p = k.load(sys.argv[2]); "
            "print(hashlib.sha256(json.dumps([c['args'] for c in k.build_cases(p)], ensure_ascii=False).encode()).hexdigest())")
    done = subprocess.run([sys.executable, "-B", "-c", code, str(HERE), str(folder)], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "PYTHONHASHSEED": hash_seed})
    return done.stdout.strip() or done.stderr[-300:]


def run(language: str, source: str, cases: list[dict], limit: float | None = None) -> list[dict]:
    """채점기로 돌린다. 케이스마다 {status, got(JSON 글 또는 None), ms}. 빌드가 안 되면 모두 그 상태다."""
    rows = [{"id": case["id"], "input": json.dumps(case["args"], ensure_ascii=False), "expected": case.get("expected", "null"),
             **({"timeout": limit} if limit and case["kind"] == "efficiency" else {})} for case in cases]
    report = judge().judge(language, source, rows, problem=FUNCTION, mode="function")
    if not report["cases"]:
        why = ((report.get("compile") or {}).get("stderr") or report.get("reason") or "")[-600:]
        return [{"status": report["status"], "got": None, "ms": 0, "why": why} for _ in cases]
    out = []
    for case in report["cases"]:
        lines = (case.get("stdout") or "").strip().splitlines()
        out.append({"status": case["status"], "got": lines[-1].strip() if lines and case["status"] in ("passed", "failed") else None,
                    "ms": case.get("time_ms", 0), "why": (case.get("stderr") or "")[-300:]})
    return out


DRIVER = """import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("m", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for line in open(sys.argv[2], encoding="utf-8"):
    print(json.dumps(m.solution(*json.loads(line)), ensure_ascii=False))
"""


def batch(path: Path, inputs: list[list], timeout: int = 180) -> list | str:
    """파이썬 풀이 하나를 입력 여러 개에 한 번에 돌린다(무작위 대조용). 결과 목록, 안 되면 까닭 글."""
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / "driver.py").write_text(DRIVER, encoding="utf-8")
        (Path(folder) / "inputs.txt").write_text("\n".join(json.dumps(args, ensure_ascii=False) for args in inputs), encoding="utf-8")
        try:
            done = subprocess.run([sys.executable, "-B", "driver.py", str(Path(path).resolve()), "inputs.txt"], cwd=folder, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            return f"{timeout}초 안에 끝나지 않았다"
    if done.returncode != 0:
        return done.stderr[-600:]
    return [json.loads(line) for line in done.stdout.strip().splitlines()]


# 해설 글(단서의 뜻·익힌 것·흔한 실수·사다리)은 고른 언어와 상관없이 같은 글을 보인다. 한 언어에만 있는 낱말(예외 이름, 내장 함수·자료형 이름)을 쓰면 다른 언어로 푸는 사용자에게 틀린 설명이 된다.
_L, _R = r"(?<![A-Za-z0-9_])", r"(?![A-Za-z0-9_])"  # \b는 한글 조사(KeyError가, heapq에서)를 낱말 글자로 봐서 쓰지 않는다
LANGUAGE_BOUND = re.compile(
    "딕셔너리|리스트(?<!인접 리스트)|튜플|파이썬|자바|코틀린|" + _L + r"(?:[A-Za-z]+(?:Error|Exception)|Python|C\+\+|Rust|dict|list|tuple|defaultdict|Counter|deque|heapq|heapify|heappush|heappop|bisect|lambda|lru_cache|sorted|setdefault|enumerate"
    r"|PriorityQueue|HashMap|BinaryHeap|priority_queue|long|int|float|double|(?:range|len|str|print|append|reverse)(?=\s*[(=]))" + _R + r"|\.(?:append|get|items|keys|values|pop|sort)\(|sys\.|\+=|-=|//")


def language_bound(problem: dict) -> list[str]:
    """해설 글에서 한 언어에만 묶인 낱말을 찾는다. 걸린 글의 목록(비면 통과). 문제 글을 따온 signals.phrase는 보지 않는다."""
    texts = {"learn": [problem["learn"]], "pattern": [problem["pattern"]], "ladder": [problem["ladder"]], "pitfalls": problem["pitfalls"], "signals.means": [s.get("means", "") for s in problem["signals"]]}
    return [f"{key}에 한 언어에만 있는 낱말 {hit.group(0)!r}: 언어와 상관없는 말로 쓴다" for key, rows in texts.items() for row in rows for hit in [LANGUAGE_BOUND.search(row)] if hit]


def ready_bound(ready: dict) -> list[str]:
    """풀이 가이드(단서·방향·단계)와 블록(이름·목표·확인·힌트)의 글에서 한 언어에만 묶인 낱말을 찾는다. 정답 코드·블록의 참고 코드·유형 id는 보지 않는다."""
    skip = {"code", "reference", "id", "kind", "patterns", "skills", "algorithm"}

    def texts(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if key not in skip:
                    yield from texts(value, f"{path}.{key}")
        elif isinstance(node, list):
            for n, value in enumerate(node):
                yield from texts(value, f"{path}[{n}]")
        elif isinstance(node, str):
            yield path, node

    return [f"ready{path}에 한 언어에만 있는 낱말 {hit.group(0)!r}: 언어와 상관없는 말로 쓴다" for path, text in texts(ready, "") for hit in [LANGUAGE_BOUND.search(text)] if hit]


GUIDE_NAME = re.compile(_L + r"(?:[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+|True|False|None)" + _R)  # 풀이 가이드가 부르는 코드 이름: 밑줄 이름(snake_case)과 파이썬 전용 값
GUIDE_LANGS = ("python", "java", "cpp", "javascript", "rust")


def guide_names(problem: dict, ready: dict) -> list[str]:
    """풀이 가이드(approach·steps·clues)가 부르는 코드 이름이 문제 글(글·제한·인자 이름)에 있거나 다섯 언어 풀이 모두에 있는지 본다. 걸린 글의 목록(비면 통과)."""
    solution = ready.get("solution") or {}
    statement = problem["statement"] + "\n" + "\n".join(problem["limits"]) + "\n" + " ".join(p["name"] for p in problem["params"])
    codes = [problem["files"].get(f"solution.{EXT[lang]}", "") for lang in GUIDE_LANGS]
    rows = [("approach", solution.get("approach") or "")] + [(f"steps[{n}]", t) for n, t in enumerate(solution.get("steps") or [])] + [(f"clues[{n}]", t) for n, t in enumerate(solution.get("clues") or [])]
    return [f"ready.solution.{key}의 이름 {name!r}이 문제 글이나 다섯 언어 풀이에 없다: 문제 글의 말로 쓴다" for key, text in rows for name in dict.fromkeys(GUIDE_NAME.findall(text))
            if name in ("True", "False", "None") or (name not in statement and not all(name in code for code in codes))]


def check(folder, langs: bool = False) -> list[str]:
    """문제 하나를 검사한다. 걸린 것의 목록(비면 통과)."""
    found: list[str] = []
    problem = load(folder)
    files, same = problem["files"], judge().common.same_value
    # 1. 모양
    for key in ("id", "theme", "level", "title", "statement", "limits", "params", "returns", "examples", "signals", "pattern", "learn", "pitfalls", "ladder"):
        if key not in problem or problem[key] in ("", [], None):
            found.append(f"problem.json에 {key}가 없거나 비었다")
    if found:
        return found
    if problem["id"] != f"{problem['theme']}_{problem['dir'].name}" or problem["dir"].parent.name != problem["theme"] or not problem["dir"].name.startswith(f"{problem['level']}_"):
        found.append("id는 <주제>_<폴더 이름>, 폴더는 <주제>/<단계>_<이름>이어야 한다")
    try:
        types = [param["type"] for param in problem["params"]]
        [parse_type(t) for t in (*types, problem["returns"])]
    except (ValueError, KeyError, TypeError) as exc:
        return [*found, f"형: {exc}"]
    text = problem["statement"] + "\n" + "\n".join(problem["limits"])
    if "solution" not in problem["statement"]:
        found.append("statement에 'solution 함수를 완성하세요'가 없다")
    if len(problem["examples"]) != 3 or any(not example.get("note") for example in problem["examples"]):
        found.append("examples는 3개이고 저마다 note(설명)가 있어야 한다")
    if not 2 <= len(problem["signals"]) <= 4:
        found.append("signals는 2~4개")
    for signal in problem["signals"]:
        if signal.get("phrase", "") not in text or not signal.get("phrase") or not signal.get("means"):
            found.append(f"실전 신호의 표현이 문제 글·제한사항에 글자 그대로 없다: {signal.get('phrase')!r}")
    found += language_bound(problem)
    saved = problem["dir"] / "ready.json"  # 풀이 가이드·블록(모델이 만들었거나 손으로 고친 것)도 같은 규칙을 지킨다
    if saved.exists():
        ready = json.loads(saved.read_text(encoding="utf-8")).get("ready") or {}
        found += ready_bound(ready) + guide_names(problem, ready)
    found += lang_check(problem)
    for name in ("solution.py", "brute.py", "gen.py"):
        if name not in files:
            found.append(f"{name}가 없다")
    wrongs = [name for name in files if name.startswith("wrong_") and name.endswith(".py")]
    slows = [name for name in files if name.startswith("slow_") and name.endswith(".py")]
    if len(wrongs) < 3:
        found.append("wrong_*.py(흔한 오답)가 3개보다 적다")
    for name in (*wrongs, *slows):
        if not files[name].startswith("# "):
            found.append(f"{name} 첫 줄에 '# 틀린 까닭: …' 또는 '# 느린 까닭: …'이 없다")
    if found:
        return found
    # 2. 케이스
    try:
        cases = build_cases(problem)
        gen = generator(problem)
        randoms = [gen["random_small"](Rng(seed_of(problem, 1000 + n))) for n in range(ROUNDS)]
    except Exception as exc:  # noqa: BLE001 - 만든 사람이 볼 까닭을 그대로 준다
        return [f"gen.py: {type(exc).__name__}: {exc}"]
    prints = {stable_print(problem["dir"], seed) for seed in ("0", "1", "12345")}
    if len(prints) != 1:  # 집합을 도는 순서처럼 실행마다 달라지는 것에 기대면 큰 입력이 채점할 때마다 바뀐다
        found.append("gen.py가 실행할 때마다 다른 입력을 만든다(문자열 집합·딕셔너리 키를 도는 순서, id(), 시각 등에 기대지 않는다. 집합은 sorted()로 돈다)")
    small = [case for case in cases if case["kind"] == "accuracy" and not case.get("medium")]
    if sum(bool(case.get("medium")) for case in cases) > MEDIUM_MAX:
        found.append(f"gen.medium은 {MEDIUM_MAX}개까지")
    large = [case for case in cases if case["kind"] == "efficiency"]
    if not SMALL[0] <= len(small) <= SMALL[1]:
        found.append(f"gen.small은 {SMALL[0]}~{SMALL[1]}개여야 한다(지금 {len(small)}개)")
    if len(large) > LARGE_MAX or bool(large) != bool(slows):
        found.append(f"효율성 케이스(LARGE)는 {LARGE_MAX}개까지이고, 있으면 slow_*.py도 있어야 한다(없으면 둘 다 없다)")
    for case in cases:
        size = len(json.dumps(case["args"], ensure_ascii=False))
        if len(case["args"]) != len(types) or not all(fits(value, typ) for value, typ in zip(case["args"], types)):
            found.append(f"케이스 {case['id']}({case['kind']})의 인자가 선언한 형과 다르다")
        elif size > (LARGE_CHARS if case["kind"] == "efficiency" else SMALL_CHARS):
            found.append(f"케이스 {case['id']}({case['kind']})가 너무 크다({size}자)")
    for args in randoms:
        if len(args) != len(types) or not all(fits(value, typ) for value, typ in zip(args, types)):
            found.append("gen.random_small이 선언한 형과 다른 인자를 만든다")
            break
    if "valid" in gen:  # (없어도 된다) 인자가 제한사항에 맞는지 만든 사람이 적어 둔 검사
        for label, args in [*((f"케이스 {case['id']}({case['kind']})", case["args"]) for case in cases), *(("무작위 입력", args) for args in randoms)]:
            try:
                ok = gen["valid"](*json.loads(json.dumps(args)))
            except Exception as exc:  # noqa: BLE001
                ok = False
                label += f" ({type(exc).__name__}: {exc})"
            if not ok:
                found.append(f"{label}가 제한사항에 맞지 않는다(gen.valid): {json.dumps(args, ensure_ascii=False)[:200]}")
                break
    seen: dict[str, dict] = {}
    for case in cases:
        first = seen.setdefault(json.dumps(case["args"], ensure_ascii=False), case)
        if first is not case:  # 공개 예시는 케이스에 자동으로 들어간다(gen.small에 다시 적으면 겹친다)
            found.append(f"같은 케이스가 두 번 들어 있다: 케이스 {first['id']}({first['kind']})와 {case['id']}({case['kind']}) — {json.dumps(case['args'], ensure_ascii=False)[:120]}")
            break
    if found:
        return found
    before, limits = saved_limits(problem), {}

    def measure(language: str, name: str, first: list[dict], share: int) -> None:
        """효율성 케이스를 한 번 더 돌려 두 번 가운데 짧은 쪽으로 제한을 정한다(기계 부하에 덜 흔들린다). 여유(제한의 1/share)도 본다."""
        again = run(language, files[name], large, LIMIT[language])
        ms = min(max(row["ms"] for case, row in zip(cases, first) if case["kind"] == "efficiency"), max(row["ms"] for row in again))
        limit, old = limit_of(language, ms / 1000), before.get(language)
        if old and abs(limit - old) <= STEP and ms <= old * 1000 / share:  # 다시 잴 때마다 조금씩 바뀌지 않게: 가까우면 지금 값을 둔다
            limit = old
        limits[language] = limit
        if ms > limit * 1000 / share:
            found.append(f"{name}가 효율성 케이스에서 {ms}ms 걸렸다(제한 {limit}초, 여유 기준 {int(limit * 1000 / share)}ms)")

    # 3. 정답 풀이 → 기대 결과
    ran = run("python", files["solution.py"], cases, LIMIT["python"])
    for case, row in zip(cases, ran):
        budget = 10 * 1000 / 3  # 효율성 케이스의 여유는 제한을 정한 뒤 본다(measure)
        if row["got"] is None:
            found.append(f"solution.py가 케이스 {case['id']}({case['kind']})에서 {row['status']}: {row['why']}")
        elif row["ms"] > budget and case["kind"] != "efficiency":
            found.append(f"solution.py가 케이스 {case['id']}({case['kind']})에서 {row['ms']}ms 걸렸다(여유 기준 {int(budget)}ms)")
        else:
            case["expected"] = row["got"]
            if not fits(json.loads(row["got"]), problem["returns"]):
                found.append(f"케이스 {case['id']}의 결과 {row['got'][:80]}가 returns 형({problem['returns']})과 다르다")
    if found:
        return found
    if large:
        measure("python", "solution.py", ran, 3)
    if found:
        return found
    # 4. 정의 그대로 풀이와 대조
    quick = [case for case in cases if case["kind"] != "efficiency" and not case.get("medium")]
    for case, row in zip(quick, run("python", files["brute.py"], quick)):
        if row["got"] is None or not same(json.loads(row["got"]), json.loads(case["expected"])):
            found.append(f"brute.py가 케이스 {case['id']}에서 다르다: 인자 {json.dumps(case['args'], ensure_ascii=False)[:200]} 정답 풀이 {case['expected'][:80]} 느린 풀이 {str(row['got'])[:80]} {row['why']}")
    fast, slow = batch(problem["dir"] / "solution.py", randoms), batch(problem["dir"] / "brute.py", randoms)
    if isinstance(fast, str) or isinstance(slow, str):
        found.append(f"무작위 대조를 돌리지 못했다: solution.py {fast if isinstance(fast, str) else '됨'} / brute.py {slow if isinstance(slow, str) else '됨'}")
    else:
        for args, a, b in zip(randoms, fast, slow):
            if not same(a, b):
                found.append(f"무작위 입력에서 두 풀이가 다르다: 인자 {json.dumps(args, ensure_ascii=False)[:300]} 정답 풀이 {json.dumps(a, ensure_ascii=False)[:80]} 느린 풀이 {json.dumps(b, ensure_ascii=False)[:80]}")
                break
        kinds = len({json.dumps(a, ensure_ascii=False) for a in fast})
        if kinds < (2 if problem["returns"] == "bool" else 3):
            found.append(f"무작위 입력 300개의 결과가 {kinds}가지뿐이다(입력이 한쪽으로 쏠렸다)")
    # 5. 오답과 느린 풀이
    for name in wrongs:
        if all(row["status"] == "passed" for row in run("python", files[name], cases, LIMIT["python"])):
            found.append(f"{name}({files[name].splitlines()[0]})가 모든 케이스를 통과한다: 이 오답을 잡는 케이스를 더한다")
    for name in slows:
        rows = run("python", files[name], cases, limits["python"])
        # 앞의 큰 정확성 케이스에서 시간 초과가 세 번 이어지면 채점기가 효율성 케이스를 돌리지 않는다(skipped). 그것도 느린 것이다
        if not any(row["status"] in ("timeout", "skipped") for case, row in zip(cases, rows) if case["kind"] == "efficiency"):
            found.append(f"{name}가 효율성 케이스에서 시간 초과하지 않는다: 입력을 키우거나 느린 풀이가 맞는지 본다")
        if any(row["status"] != "passed" for case, row in zip(cases, rows) if case["kind"] != "efficiency" and not case.get("medium")):
            found.append(f"{name}가 정확성 케이스에서 틀린다(느린 풀이는 답이 맞아야 한다)")
    # 6. 다른 언어
    if langs:
        for language, ext in EXT.items():
            name = f"solution.{ext}"
            if language == "python" or name not in files:
                continue
            ran = run(language, files[name], cases, LIMIT[language])
            bad = next(((case, row) for case, row in zip(cases, ran) if row["status"] != "passed"), None)
            if bad:
                found.append(f"{name}가 케이스 {bad[0]['id']}({bad[0]['kind']})에서 {bad[1]['status']}: {str(bad[1]['got'])[:80]} {bad[1]['why']}")
            elif large:
                measure(language, name, ran, 2)  # 다른 언어는 제한이 짧아 여유를 절반으로 본다
    ran_langs = [language for language in EXT if language == "python" or langs]
    if not found:  # 7. 언어 함정(파이썬은 늘, 다른 언어는 --langs일 때 돌린다)
        proofs, found = lang_run(problem, cases, ran_langs, {**before, **limits})
    if not found:
        frozen = [{"id": case["id"], "kind": case["kind"], "expected": case["expected"],
                   **({"gen": case["gen"]} if case["kind"] == "efficiency" else {"input": json.dumps(case["args"], ensure_ascii=False)})} for case in cases]
        frozen_text = json.dumps(frozen, ensure_ascii=False, indent=1) + "\n"
        write_lang(problem, proofs, ran_langs, frozen_text)
        (problem["dir"] / "cases.json").write_text(frozen_text, encoding="utf-8")
        if large:  # --langs 없이 돌렸으면 잰 Python만 바꾸고 다른 언어의 값은 그대로 둔다
            kept = {**before, **limits}
            saved = {language: kept[language] for language, ext in EXT.items() if language in kept and f"solution.{ext}" in files}
            (problem["dir"] / "limits.json").write_text(json.dumps(saved) + "\n", encoding="utf-8")
    return found


def frozen_cases(problem: dict) -> list[dict]:
    """cases.json(검사를 통과할 때 얼린 케이스)을 인자까지 되살린다. 큰 입력은 다시 만든다."""
    gen = None
    rows = []
    for row in json.loads((problem["dir"] / "cases.json").read_text(encoding="utf-8")):
        if "gen" in row:
            gen = gen or generator(problem)
            rows.append({**row, "args": large_args(problem, row["gen"], gen)})
        else:
            rows.append({**row, "args": json.loads(row["input"])})
    return rows


def attempt(folder, path) -> bool:
    """풀이 파일 하나를 얼린 케이스 전부에 돌려 본다(언어는 확장자로). 검수자와 다른 언어 풀이를 쓰는 사람이 쓴다."""
    problem, path = load(folder), Path(path)
    language = {ext: name for name, ext in EXT.items()}[path.suffix.lstrip(".")]
    cases = frozen_cases(problem)
    limit = saved_limits(problem).get(language, LIMIT[language])  # 서버와 같은 제한
    rows = run(language, path.read_text(encoding="utf-8"), cases, limit)
    good = sum(row["status"] == "passed" for row in rows)
    print(f"{problem['id']} {path.name}({language}): {good}/{len(rows)} 통과, 가장 오래 걸린 케이스 {max(row['ms'] for row in rows)}ms(효율성 제한 {limit}초)")
    for case, row in zip(cases, rows):
        if row["status"] != "passed":
            shown = case["input"][:300] if "input" in case else f"(효율성 케이스 {case['gen']}번: 큰 입력)"
            print(f"  - 케이스 {case['id']}({case['kind']}) {row['status']}: 인자 {shown} 기대 {case['expected'][:120]} 나온 값 {str(row['got'])[:120]} {row['why'][-300:]}")
    return good == len(rows)


# 언어 함정: 해설의 정답 코드 위에 '이 언어에서 조심할 것'을 보인다. 보일 글은 목록(problems/lang_traps.json) 한 곳에만 있다.
# 문제 폴더의 lang_<번호>.<확장자>는 정답 풀이에 그 실수 하나만 넣은 풀이이고, 이 문제의 케이스에서 실제로 떨어져야 한다(증명).
TRAPS = HERE / "problems" / "lang_traps.json"
TRAP_RULES = HERE.parent / "tutor" / "debug" / "rules.py"


@functools.cache
def trap_rules():
    """증명을 얼리고 확인하는 판정(돌려준 값의 꼴, 모양 식). 튜터가 후보를 거르는 것과 같은 파일을 judge()처럼 경로로 읽는다:
    튜터 묶음(tutor/__init__)을 부르지 않아 langgraph 없이 돌고, 쓰는 함수 안에서만 읽어 서버(fits만 쓴다)는 이 파일을 읽지 않는다."""
    spec = importlib.util.spec_from_file_location("algoblock_trap_rules", TRAP_RULES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
TRAP_MAX, TRAP_CHARS, TRAP_FILES, TRAP_LINES, TRAP_AT = 12, 80, 3, 6, 2  # 언어마다 항목 수, what·fix 길이, 문제·언어마다 증명 파일 수, 넣은 줄·지운 줄 수, 구절 수
TRAP_KEYS = ("id", "what", "fix", "code", "right", "recipe")  # 그 밖에 "varies": true(결과가 정해지지 않은 동작이라 떨어지는 케이스가 기기마다 다를 수 있다)
# 그리고 "shape": 실수의 모양 식(정규식, 주석 밖 코드에 맞춘다). 이름만으로 다른 버그와 가를 수 없을 때 둔다. varies 함정은 이것이 없으면 튜터가 후보로 내지 않는다
# 어느 풀이에나 흔한 낱말과 한 글자 기호는 닻(증명 파일이 그 실수를 넣었다는 표시)으로 세지 않는다. 우연히 바뀐 줄로 통과하지 않게
COMMON = frozenset({"for", "while", "if", "else", "return", "in", "of", "get", "set", "new", "let", "const", "var", "def", "fn", "function", "int", "auto"})
FALLS = ("failed", "runtime_error", "timeout", "memory_limit")  # 떨어진 상태. 건너뜀(skipped)은 근거로 얼리지 않고, 빌드가 안 된 것(컴파일 오류 등)은 증명이 아니다
LANG_FILE = re.compile(r"lang_\d+\.([a-z]+)")
TRAP_HEAD = re.compile(r'(?:#|//) 언어 함정: ([a-z]+\.[a-z0-9_]+)(?: @((?: "[^"]+"){1,2}))?')


def traps() -> dict:
    """함정 목록 {언어: [{id, what, fix, code, right, recipe, varies?}]}. 없으면 빈 것."""
    return json.loads(TRAPS.read_text(encoding="utf-8")) if TRAPS.is_file() else {}


def has_term(term: str, text: str) -> bool:
    """글에 이름이 있는가. 낱말 글자로 시작·끝나는 이름은 다른 낱말의 일부(print 속의 int)로 세지 않는다."""
    return re.search((_L if re.match(r"\w", term[0]) else "") + re.escape(term) + (_R if re.match(r"\w", term[-1]) else ""), text) is not None


def anchor(term: str) -> bool:
    return len(term) >= 2 and term not in COMMON


def proof_files(problem: dict) -> list[tuple[str, str, str, tuple]]:
    """문제 폴더의 증명 파일: (파일 이름, 언어, 함정 id, 구절들). 모르는 확장자면 언어가, 첫 줄을 못 읽으면 id가 빈 글이다."""
    language_of = {ext: language for language, ext in EXT.items()}
    out = []
    for name in sorted(problem["files"]):
        match = LANG_FILE.fullmatch(name)
        if match:
            head = TRAP_HEAD.fullmatch(problem["files"][name].split("\n", 1)[0].strip())
            out.append((name, language_of.get(match[1], ""), head[1] if head else "", tuple(re.findall(r'"([^"]+)"', head[2] or "")) if head else ()))
    return out


def code_lines(text: str) -> Counter:
    return Counter(line.strip() for line in text.splitlines() if line.strip())


def lang_check(problem: dict, listed: dict | None = None) -> list[str]:
    """증명 파일의 모양(채점기 없이): 첫 줄, 목록에 있는 id, 문제 글의 구절, 바꾼 줄(닻·좁힘), 파일 수."""
    listed, files, found, seen = traps() if listed is None else listed, problem["files"], [], {}
    text = problem["statement"] + "\n" + "\n".join(problem["limits"])
    for name, language, trap, phrases in proof_files(problem):
        solution = files.get(f"solution.{EXT.get(language, '')}")
        mark = "#" if language == "python" else "//"
        row = next((row for row in listed.get(language, []) if isinstance(row, dict) and row.get("id") == trap), None)
        if solution is None:
            found.append(f"{name}: 같은 언어의 정답 풀이(solution.<확장자>)가 없다")
            continue
        if not trap or not files[name].startswith(mark + " "):
            found.append(f"{name} 첫 줄이 '{mark} 언어 함정: <목록의 id>' 또는 '{mark} 언어 함정: <목록의 id> @ \"구절\"'(구절은 둘까지)이 아니다")
            continue
        if row is None:
            found.append(f"{name}: {trap}가 lang_traps.json의 {language} 목록에 없다")
            continue
        found += [f"{name}: 구절 {phrase!r}가 문제 글·제한사항에 글자 그대로 없다" for phrase in phrases if phrase not in text]
        seen.setdefault(language, []).append(trap)
        proof, base = code_lines(files[name].split("\n", 1)[1] if "\n" in files[name] else ""), code_lines(solution)
        added, removed = list((proof - base).elements()), list((base - proof).elements())
        if not added and not removed:
            found.append(f"{name}: 정답 풀이와 같다(실수 하나를 넣는다)")
        elif len(added) > TRAP_LINES or len(removed) > TRAP_LINES:
            found.append(f"{name}: 정답 풀이에서 넣은 줄 {len(added)}개, 지운 줄 {len(removed)}개다(각 {TRAP_LINES}개까지. 실수 하나만 넣는다)")
        put = any(anchor(term) and any(has_term(term, line) for line in added) and not any(has_term(term, line) for line in removed) for term in row["code"])
        took = any(anchor(term) and any(has_term(term, line) for line in removed) and not any(has_term(term, line) for line in added) for term in row["right"])
        if not put and not took:
            found.append(f"{name}: 바꾼 줄에 {trap}의 표시가 없다(넣은 줄에만 있는 code {row['code']}, 또는 지운 줄에만 있는 right {row['right']}. 흔한 낱말과 한 글자는 세지 않는다)")
        if not any(has_term(term, solution) for term in row["right"]):
            found.append(f"{name}: 정답 풀이에 {trap}의 right {row['right']} 가운데 하나도 없다")
        if isinstance(row.get("shape"), str) and not _shape_ok(row, files[name], solution):
            found.append(f"{name}: {trap}의 모양 식(shape)이 증명 풀이에는 맞고 정답 풀이에는 맞지 않아야 한다")
    for language, ids in seen.items():
        if len(ids) > TRAP_FILES:
            found.append(f"{language} 증명 파일이 {len(ids)}개다({TRAP_FILES}개까지)")
        if len(set(ids)) < len(ids):
            found.append(f"{language}에서 같은 함정을 증명 파일 둘이 보인다")
    return found


def _shape_ok(row: dict, proof: str, solution: str) -> bool:
    """모양 식이 증명 풀이에는 맞고 정답 풀이에는 맞지 않는가."""
    return trap_rules().shape_in(row, proof) and not trap_rules().shape_in(row, solution)


def lang_run(problem: dict, cases: list[dict], languages: list[str], limits: dict, listed: dict | None = None) -> tuple[dict, list[str]]:
    """그 언어들의 증명 파일을 케이스 전부에 돌린다. ({언어: [lang.json의 행]}, 걸린 것). 모든 케이스를 통과하면 증명이 아니다.
    결과가 정해지지 않은 동작의 함정(varies)은 떨어진 케이스 목록 대신 떨어졌다는 것만 남긴다(기기마다 다를 수 있다)."""
    varies = {row["id"] for rows in (traps() if listed is None else listed).values() for row in rows if isinstance(row, dict) and row.get("varies")}
    rows, found = {}, []
    for name, language, trap, phrases in proof_files(problem):
        if language not in languages:
            continue
        ran = run(language, problem["files"][name], cases, limits.get(language) or LIMIT[language])
        fails = {case["id"]: row["status"] for case, row in zip(cases, ran) if row["status"] not in ("passed", "skipped")}
        outs = {case["id"]: trap_rules().out_key(row["got"]) for case, row in zip(cases, ran) if row["status"] == "failed"}  # 틀린 답은 돌려준 값까지(같은 케이스에서 틀리는 다른 버그와 가른다)
        odd = sorted(set(fails.values()) - set(FALLS))
        if not fails:
            found.append(f"{name}({trap})가 모든 케이스를 통과한다: 이 문제에서는 증명되지 않으니 파일을 지운다")
        elif odd:
            found.append(f"{name}({trap})를 돌리지 못했다({', '.join(odd)}): 증명 파일은 빌드되고 실행돼야 한다 {ran[0]['why'][-300:]}")
        else:
            rows.setdefault(language, []).append({"file": name, "trap": trap, **({"at": list(phrases)} if phrases else {}), **({"varies": True} if trap in varies else {"fails": fails, **({"outs": outs} if outs else {})})})
    return rows, found


def proof_source(problem: dict, name: str, cases_text: str) -> int:
    """증명 파일 본문과 얼린 케이스의 지문. 둘 중 하나가 바뀌면 lang.json의 그 행은 낡은 것이다."""
    return zlib.crc32((problem["files"][name] + "\n" + cases_text).encode())


def write_lang(problem: dict, proofs: dict, ran: list[str], cases_text: str) -> None:
    """lang.json을 쓴다. 이번에 돌리지 않은 언어는 지난 값을 두되, 지금 없거나 본문·케이스가 바뀐 파일의 행은 뺀다. 증명이 하나도 없으면 지운다."""
    path = problem["dir"] / "lang.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    fresh = {language: [{**row, "source": proof_source(problem, row["file"], cases_text)} for row in rows] for language, rows in proofs.items()}
    kept = {language: [row for row in rows if row["file"] in problem["files"] and row.get("source") == proof_source(problem, row["file"], cases_text)]
            for language, rows in old.items() if language not in ran}
    out = {language: fresh.get(language) or kept.get(language) for language in EXT if fresh.get(language) or kept.get(language)}
    if out:
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    elif path.exists():
        path.unlink()


def lang_frozen(problem: dict) -> list[str]:
    """lang.json(지난 검사가 얼린 것)이 지금의 증명 파일·케이스와 맞는가(채점기 없이). 이름·id·구절과 본문·케이스의 지문을 견준다."""
    path, cases = problem["dir"] / "lang.json", problem["dir"] / "cases.json"
    saved = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    cases_text = cases.read_text(encoding="utf-8") if cases.is_file() else ""
    outs = lambda row: set(row.get("outs") or {}) == {cid for cid, status in (row.get("fails") or {}).items() if status == "failed"}  # 틀린 답의 케이스마다 돌려준 값이 얼려 있다
    have = sorted((row["file"], language, row["trap"], tuple(row.get("at", []))) for language, rows in saved.items() for row in rows
                  if (row.get("fails") or row.get("varies")) and outs(row) and row["file"] in problem["files"] and row.get("source") == proof_source(problem, row["file"], cases_text))
    return [] if have == proof_files(problem) else ["lang.json이 증명 파일(lang_*)이나 케이스와 다르다: check(다른 언어는 --langs)로 다시 쓴다"]


def trap_list_check(listed: dict | None = None, root: Path = HERE / "problems") -> list[str]:
    """함정 목록의 모양, 그리고 쓰는 증명 파일이 하나도 없는 항목(증명 없는 글은 두지 않는다). 채점기 없이 본다."""
    listed = traps() if listed is None else listed
    used = {head[1] for path in root.glob("*/*/lang_*.*") for head in [TRAP_HEAD.fullmatch(path.read_text(encoding="utf-8").split("\n", 1)[0].strip())] if head}
    found, ids = [], []
    if not isinstance(listed, dict):
        return ["lang_traps.json: {언어: [항목]} 꼴이 아니다"]
    for language, rows in listed.items():
        if language not in EXT or not isinstance(rows, list):
            found.append(f"lang_traps.json: {language!r}는 언어가 아니거나 항목 목록이 아니다")
            continue
        if len(rows) > TRAP_MAX:
            found.append(f"lang_traps.json: {language} 항목이 {len(rows)}개다({TRAP_MAX}개까지)")
        for row in rows:
            row = row if isinstance(row, dict) else {}
            texts = all(isinstance(row.get(key), str) and row[key].strip() for key in ("id", "what", "fix", "recipe"))
            names = all(isinstance(row.get(key), list) and all(isinstance(term, str) and term for term in row[key]) for key in ("code", "right")) and bool(row.get("right"))
            if not set(TRAP_KEYS) <= set(row) <= {*TRAP_KEYS, "varies", "shape"} or not texts or not names or row.get("varies", True) is not True:
                found.append(f"lang_traps.json: {language}의 {row.get('id')!r}: 칸은 {', '.join(TRAP_KEYS)}(그리고 varies: true, shape)이고, 글은 비지 않고, "
                             "code는 이름 목록(비어도 된다), right는 대안 이름 목록(하나 이상)이다")
                continue
            if "shape" in row:
                try:
                    re.compile(row["shape"])
                except (re.error, TypeError):
                    found.append(f"lang_traps.json: {row['id']}의 shape가 정규식이 아니다")
            trap = row["id"]
            ids.append(trap)
            if not trap.startswith(language + ".") or not TRAP_HEAD.fullmatch(f"# 언어 함정: {trap}"):
                found.append(f"lang_traps.json: {trap}: id는 '{language}.<소문자·숫자·_>'이다")
            for key in ("what", "fix"):
                if len(row[key]) > TRAP_CHARS:
                    found.append(f"lang_traps.json: {trap}의 {key}가 {len(row[key])}자다({TRAP_CHARS}자까지)")
            if not re.search(r"`[^`]+`", row["what"]):
                found.append(f"lang_traps.json: {trap}의 what에 백틱으로 감싼 이름이 없다")
            if any(has_term(term, row["what"]) for term in row["right"]):
                found.append(f"lang_traps.json: {trap}의 what에 고치는 이름(right)이 있다: 고치는 법은 fix에 쓴다")
            if not any(anchor(term) for term in (*row["code"], *row["right"])):
                found.append(f"lang_traps.json: {trap}: code·right에 닻으로 쓸 이름이 없다(두 글자 이상, 흔한 낱말 {sorted(COMMON)}이 아닌 것)")
            if trap not in used:
                found.append(f"lang_traps.json: {trap}를 증명하는 파일(lang_*)이 없다: 증명 없는 글은 두지 않는다")
    found += [f"lang_traps.json: id {trap}가 두 번 있다" for trap in sorted({trap for trap in ids if ids.count(trap) > 1})]
    return found


def folders(paths: list[str]) -> list[Path]:
    out = []
    for path in map(Path, paths):
        out += [path] if (path / "problem.json").is_file() else sorted(p.parent for p in path.rglob("problem.json"))
    return out


def main() -> None:
    command, rest = sys.argv[1], [arg for arg in sys.argv[2:] if not arg.startswith("--")]
    if command == "stub":
        from stubs import stub  # 시작 코드(언어별 함수 틀)

        print(stub(load(rest[0]), rest[1]))
        return
    if command == "try":  # python3 ui/problemkit.py try <문제 폴더> <풀이 파일>
        sys.exit(0 if attempt(rest[0], rest[1]) else 1)
    bad = 0
    for folder in folders(rest):
        found = check(folder, langs="--langs" in sys.argv)
        bad += bool(found)
        print(f"{'통과' if not found else '실패'} {folder}")
        for line in found:
            print(f"  - {line}")
    listed = trap_list_check()  # 목록은 모든 문제의 증명 파일과 견준다(어느 폴더를 검사하든 같다)
    bad += bool(listed)
    print(f"{'통과' if not listed else '실패'} {TRAPS.name}")
    for line in listed:
        print(f"  - {line}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
