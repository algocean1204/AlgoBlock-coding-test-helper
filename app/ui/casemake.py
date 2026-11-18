"""등록한 문제의 케이스 만들기. 모델이 쓴 정답 풀이·단순 풀이·케이스 생성기를 대조한다. 모델을 부르지 않는다.

세 코드 모두 채점기(따로 뜨는 프로세스: 제한 시간·CPU·메모리 상한, 비밀 환경 변수 가리기)로만 돌린다. 이 프로세스에서 exec·eval·import하지 않는다.
기본 문제의 검수(problemkit.check)와 같은 생각이다: 정의 그대로 푼 풀이와 맞는 입력만 숨은 케이스가 되고, 큰 입력은 정답 풀이가 걸린 시간에서 제한을 정한다.
"""

import json
import re
import sys
from itertools import zip_longest

from casegen import LIMIT, limit_of
from tutor.eval.drive import check_judge as judge  # 서버와 같은 채점기(설치 파일에서는 ALGOBLOCK_JUDGE_DIR)
from problemkit import LARGE_CHARS, SMALL_CHARS

HIDDEN_MAX = 20  # 숨은 정확성 케이스 수 상한
LARGE_MAX = 3  # 효율성 케이스 수 상한
INPUTS_MAX = 60  # 대조할 작은·경계 입력 수 상한
AGREE_MIN = 5  # 두 풀이가 이보다 적은 입력에서만 끝났으면 대조하지 못한 것이다
NOT_MADE = "테스트 입력을 자동으로 만들지 못했어요. 문제의 제한사항을 확인해 주세요."
RUN_SECONDS = 5  # 작은 입력 하나의 제한(단순 풀이는 느려도 된다)
GEN_SECONDS = 20  # 생성기 한 번의 제한
FUNCTION = "solution 함수를 완성하세요"
ORDER = (("edge", "edge"), ("tricky", "tricky"), ("small", "random"))  # (생성기 함수, 케이스 꼬리표). 숨은 케이스는 이 차례로 돌아가며 뽑는다

# 생성기 뒤에 앱이 붙인다: 표준 입력으로 받은 종류(small·edge·tricky·large n)의 입력을 한 줄에 하나씩 JSON으로 쓴다. 씨앗을 정해 다시 돌려도 같다.
# tricky()가 없는 생성기(예전 생성기)는 빈 목록이다. 큰 입력은 하나씩 따로 돌린다(채점기의 출력 상한 4MB를 입력 하나가 거의 다 쓸 수 있다)
DRIVER = """

if __name__ == "__main__":
    import json as _json, random as _random, sys as _sys
    _random.seed(20261113)
    _kind, *_at = _sys.stdin.read().split()
    _made = {"small": small, "edge": edge, "tricky": globals().get("tricky", list), "large": large}[_kind]()
    for _one in _made[int(_at[0]):int(_at[0]) + 1] if _at else _made:
        print(_json.dumps(_one, ensure_ascii=False))
"""


def outputs(language: str, source: str, inputs: list, mode: str, seconds: float, stop: int | None = None) -> list:
    """입력마다 (상태, 출력). 출력은 끝까지 돈 것만(함수 방식은 마지막 줄의 JSON 값, 표준 입출력은 출력 글 전체), 아니면 None.
    stop: 연속 시간 초과가 이만큼이면 남은 입력을 돌리지 않는다(없으면 모두 돌린다)."""
    rows = [{"id": str(n), "input": json.dumps(x, ensure_ascii=False) if mode == "function" else x, "expected": "null" if mode == "function" else ""}
            for n, x in enumerate(inputs, 1)]
    report = judge().judge(language, source, rows, problem=FUNCTION if mode == "function" else "", mode=mode, timeout=seconds, stop_after=stop or len(rows) + 1)
    if not report["cases"]:
        why = ((report.get("compile") or {}).get("stderr") or report.get("reason") or report["status"])[-300:]
        return [(report["status"], None, why)] * len(inputs)
    out = []
    for case in report["cases"]:
        ran = case["status"] in ("passed", "failed")
        text = case.get("stdout") or ""
        if ran and mode == "function":
            lines = text.strip().splitlines()
            try:
                value = json.loads(lines[-1]) if lines else None
            except ValueError:
                ran, value = False, None
            out.append(("passed" if ran else "bad_output" if case["status"] in ("passed", "failed") else case["status"], value if ran else None, (case.get("stderr") or "")[-300:]))
        else:
            out.append((case["status"] if not ran else "passed", text if ran else None, (case.get("stderr") or "")[-300:]))
    return out


def generate(maker: str) -> dict | str:
    """생성기를 채점기로 돌려 {small, edge, tricky, large: [입력]}. 안 되면 화면에 보일 한 문장(어느 함수가 어떻게 실패했는지는 표준 오류에만 적는다).
    tricky()만 실패하면 함정 입력 없이 나머지로 간다."""
    found = {"small": [], "edge": [], "tricky": [], "large": []}
    kinds = ["small", "edge", "tricky", *(f"large {n}" for n in range(LARGE_MAX))]
    for kind, (status, text, why) in zip(kinds, outputs("python", maker + DRIVER, [kind + "\n" for kind in kinds], "program", GEN_SECONDS)):
        if text is None:
            print(f"[casemake] {kind.split()[0]}() {status}: {why}", file=sys.stderr)
            if kind == "tricky":
                continue
            return NOT_MADE
        try:
            found[kind.split()[0]] += [json.loads(line) for line in text.splitlines() if line.strip()]
        except ValueError:
            print(f"[casemake] {kind.split()[0]}() 출력을 읽지 못함", file=sys.stderr)
            return NOT_MADE
    return found


def numbers(value) -> list:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [value]
    if isinstance(value, list):
        return [n for item in value for n in numbers(item)]
    return []


def fits(one, bounds: list, mode: str, arity: int | None) -> bool:
    """생성된 입력 하나가 모양과 제한사항(생성기가 적은 bounds)을 지키는가. 규칙만 본다(생성기 코드를 다시 믿지 않는다)."""
    if mode == "program":
        if not isinstance(one, str):
            return False
        args = [[int(token) for token in re.findall(r"-?\d+", one)]]
    else:
        if not isinstance(one, list) or (arity is not None and len(one) != arity):
            return False
        args = one
    for bound in bounds:
        if not 0 <= bound.arg < len(args):
            continue
        value = args[bound.arg]
        if any((bound.low is not None and n < bound.low) or (bound.high is not None and n > bound.high) for n in numbers(value)):
            return False
        if mode == "function" and isinstance(value, (list, str)) and (
                (bound.shortest is not None and len(value) < bound.shortest) or (bound.longest is not None and len(value) > bound.longest)):
            return False
    return True


def same(a, b, mode: str, decimal: bool = False) -> bool:
    common = judge().common
    return common.same_value(a, b) if mode == "function" else common.same_program_output(a, b, decimal)


def shown(value, mode: str) -> str:
    return json.dumps(value, ensure_ascii=False) if mode == "function" else str(value)


def make(language: str, mode: str, code: str, brute: str, maker: str, bounds: list, arity: int | None = None, decimal: bool = False) -> dict:
    """정답 풀이(code, 그 언어)와 단순 풀이(brute, python)를 생성기의 입력에서 대조한다. decimal: 표준 입출력 문제가 실수 답을 허용한다(채점과 같은 비교).
    {status: same(맞다: hidden·large가 케이스) | differ(다른 입력: input·got·want) | error(대조하지 못함: why), dropped: 제한사항을 어겨 버린 입력 수, …}.
    same이면 tags(hidden마다 edge·tricky·random), counts(종류별 수와 efficiency), indistinct(단순 풀이도 큰 입력을 모두 끝냈다: 효율성으로 가리지 못함)도 준다."""
    made = generate(maker)
    if isinstance(made, str):
        return {"status": "error", "why": made}
    total = sum(len(made[kind]) for kind in made)
    tagged = [(tag, x) for kind, tag in ORDER for x in made[kind] if fits(x, bounds, mode, arity)]  # 함정 입력도 같은 검사를 거친다
    large = [x for x in made["large"] if fits(x, bounds, mode, arity)]
    dropped = total - len(tagged) - len(large)
    large = [x for x in large if len(shown(x, mode)) <= LARGE_CHARS][:LARGE_MAX]
    first: dict = {}
    for tag, x in tagged:  # 같은 입력은 앞 종류(경계 → 함정 → 무작위)의 것으로 한 번만
        first.setdefault(shown(x, mode), (tag, x))
    unique = list(first.values())[:INPUTS_MAX]
    if not unique:
        return {"status": "error", "why": "제한사항에 맞는 테스트 입력을 만들지 못했어요.", "dropped": dropped}
    inputs = [x for _, x in unique]
    mine, ref = outputs(language, code, inputs, mode, RUN_SECONDS), outputs("python", brute, inputs, mode, RUN_SECONDS)
    agreed = []
    for (tag, x), (status, a, why), (_, b, _) in zip(unique, mine, ref):
        if b is None:  # 단순 풀이가 끝내지 못한 입력은 대조하지 않는다(느려도 되는 풀이다)
            continue
        if a is None or not same(a, b, mode, decimal):
            return {"status": "differ", "input": shown(x, mode)[:600], "got": (shown(a, mode) if a is not None else f"{status} {why}")[:300],
                    "want": shown(b, mode)[:300], "dropped": dropped}
        agreed.append((tag, x, b))
    if len(agreed) < AGREE_MIN:
        return {"status": "error", "why": f"비교할 수 있는 입력이 {len(agreed)}개뿐이라 검증을 끝내지 못했어요.", "dropped": dropped}
    groups = [[one for one in agreed if one[0] == tag and len(shown(one[1], mode)) <= SMALL_CHARS] for _, tag in ORDER]
    picked = [one for row in zip_longest(*groups) for one in row if one is not None][:HIDDEN_MAX]  # 경계 → 함정 → 무작위로 돌아가며. 바닥난 종류는 건너뛴다
    hidden, tags = [(shown(x, mode), shown(b, mode)) for _, x, b in picked], [tag for tag, _, _ in picked]
    big, seconds, indistinct = [], 0.0, False
    if large:
        report = judge().judge(language, code, [{"id": str(n), "input": shown(x, mode), "expected": "null" if mode == "function" else ""} for n, x in enumerate(large, 1)],
                               problem=FUNCTION if mode == "function" else "", mode=mode, timeout=LIMIT[language], stop_after=len(large) + 1)
        for x, case in zip(large, report["cases"]):
            if case["status"] not in ("passed", "failed"):
                return {"status": "differ", "input": "(제한사항의 가장 큰 입력)", "got": f"{case['status']}: {LIMIT[language]}초 안에 끝나지 않았거나 실행 오류",
                        "want": "제한 시간 안에 끝나는 풀이", "slow": True, "dropped": dropped}
            lines = (case.get("stdout") or "").strip().splitlines()
            big.append((shown(x, mode), (lines[-1].strip() if lines else "") if mode == "function" else case.get("stdout") or ""))
            seconds = max(seconds, case.get("time_ms", 0) / 1000)
        # 단순 풀이(느린 풀이의 대표)도 큰 입력을 모두 Python 상한 안에 끝내면 효율성 케이스가 느린 풀이를 가리지 못한다.
        # 상한: 입력마다 LIMIT["python"]초, 처음 끝나지 않은 입력에서 멈춘다(가리는 입력이 하나면 된다). 그래서 이 확인은 많아야 LARGE_MAX × 그 상한이다
        indistinct = all(text is not None for _, text, _ in outputs("python", brute, large, mode, LIMIT["python"], stop=1))
    # 한계: 효율성 케이스를 한 번만 잰다(problemkit은 두 번 재 짧은 쪽). 제한이 흔들리면 두 번 잰다
    counts = {**{tag: tags.count(tag) for _, tag in ORDER}, "efficiency": len(big)}
    return {"status": "same", "hidden": hidden, "tags": tags, "counts": counts, "indistinct": indistinct, "large": big,
            "limit": limit_of(language, seconds) if big else None, "dropped": dropped}
