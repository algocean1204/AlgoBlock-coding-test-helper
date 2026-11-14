"""디버그 진단 측정: 1단계 사용자가 실제로 내는 틀린 코드에서 원인 줄·함정을 맞게 짚는가, 고친 줄을 넣으면 통과하는가.

python3 -m tutor.eval.bench locate [--cli]
온톨로지 함정 후보를 준 것과 안 준 것을 같이 잰다(ALGOBLOCK_BENCH_NO_ONTOLOGY=1이면 후보 없이).
"""

import os
import time

from ..debug import nodes, rules
from ..llm.themes import pick
from ..state import TutorContext, TutorRequest
from .drive import check_judge, debug_report
from .scenarios import by_id

H = "def solution(borrowed, returned):\n"
S = "def solution(s):\n"
C = "def solution(cards, target):\n"

# (id, 시나리오, 패턴, 코드, 원인 줄(허용 줄들), 받아 주는 함정 id들, 한 줄 고침으로 통과할 수 있는가)
BUGS = [
    ("key_missing", "hash_library", ["dup_names"], H + "    count = {}\n    for name in borrowed:\n        count[name] += 1\n    for name in returned:\n        count[name] -= 1\n    for name in count:\n        if count[name] > 0:\n            return name\n", [4], ["key_missing", "wrong_init"], True),
    ("exists_only", "hash_library", ["dup_names"], H + "    for name in borrowed:\n        if name not in returned:\n            return name\n", [3], ["exists_not_count"], False),
    ("no_colon", "hash_library", ["dup_names"], H + "    count = {}\n    for name in borrowed\n        count[name] = count.get(name, 0) + 1\n    for name in returned:\n        count[name] -= 1\n    for name in count:\n        if count[name] > 0:\n            return name\n", [3], ["missing_colon"], True),
    ("reset_in_loop", "hash_library", ["dup_names"], H + "    for name in borrowed:\n        count = {}\n        count[name] = count.get(name, 0) + 1\n    for name in returned:\n        count[name] -= 1\n    for name in count:\n        if count[name] > 0:\n            return name\n", [3], ["wrong_init"], False),
    ("count_only", "stack_brackets", ["recent_first"], S + "    if s.count('(') == s.count(')') and s.count('[') == s.count(']'):\n        return True\n    return False\n", [2], ["count_not_order"], False),
    ("empty_pop", "stack_brackets", ["recent_first"], S + "    pair = {')': '(', ']': '['}\n    stack = []\n    for ch in s:\n        if ch in '([':\n            stack.append(ch)\n        else:\n            if stack.pop() != pair[ch]:\n                return False\n    return not stack\n", [8], ["empty_pop"], True),
    ("leftover", "stack_brackets", ["recent_first"], S + "    pair = {')': '(', ']': '['}\n    stack = []\n    for ch in s:\n        if ch in '([':\n            stack.append(ch)\n        else:\n            if not stack or stack.pop() != pair[ch]:\n                return False\n    return True\n", [10], ["leftover_unchecked", "missed_case"], True),
    ("assign_eq", "stack_brackets", ["recent_first"], S + "    stack = []\n    for ch in s:\n        if ch = '(' or ch == '[':\n            stack.append(ch)\n        elif not stack:\n            return False\n        else:\n            top = stack.pop()\n            if (ch == ')' and top != '(') or (ch == ']' and top != '['):\n                return False\n    return len(stack) == 0\n", [4], ["assign_vs_equal"], True),
    ("pair_twice", "brute_pairs", ["choose_two_small_n"], C + "    answer = 0\n    for i in range(len(cards)):\n        for j in range(len(cards)):\n            if cards[i] + cards[j] == target:\n                answer += 1\n    return answer\n", [4], ["pair_twice"], True),
    ("early_return", "brute_pairs", ["choose_two_small_n"], C + "    answer = 0\n    for i in range(len(cards)):\n        for j in range(i + 1, len(cards)):\n            if cards[i] + cards[j] == target:\n                answer += 1\n        return answer\n", [7], ["early_return", "indent"], True),
    ("typo_name", "brute_pairs", ["choose_two_small_n"], C + "    answer = 0\n    for i in range(len(cards)):\n        for j in range(i + 1, len(cards)):\n            if cards[i] + cards[j] == target:\n                anwser += 1\n    return answer\n", [6], ["undefined_name"], True),
    ("off_by_one", "brute_pairs", ["choose_two_small_n"], C + "    answer = 0\n    for i in range(len(cards)):\n        for j in range(i + 1, len(cards) - 1):\n            if cards[i] + cards[j] == target:\n                answer += 1\n    return answer\n", [4], ["off_by_one"], True),
]


def patched(code: str, line: int, fixed: str) -> str:
    """진단이 낸 고친 줄을 그 줄에 넣는다. 들여쓰기가 없으면 원래 줄의 것을 쓴다."""
    lines = code.splitlines()
    if not 1 <= line <= len(lines) or not fixed.strip():
        return code
    old = lines[line - 1]
    lines[line - 1] = fixed if fixed[:1] in " \t" else old[: len(old) - len(old.lstrip())] + fixed.strip()
    return "\n".join(lines) + "\n"


def locate_one(item) -> dict:
    name, sid, patterns, code, lines, pitfalls, one_line = item
    scenario = by_id(sid)
    report = debug_report(scenario, code)
    assert report["status"] != "passed", name
    ctx = TutorContext(problem_id=sid, problem_text=scenario.text, language="python",
                       patterns=[] if os.environ.get("ALGOBLOCK_BENCH_NO_ONTOLOGY") else patterns)
    state = {"ctx": ctx, "request": TutorRequest(kind="debug", problem_id=sid, code=code, report=report)}
    state["draft"] = nodes.gather(state)["draft"]
    if os.environ.get("ALGOBLOCK_BENCH_NO_ONTOLOGY"):
        state["draft"]["candidates"] = []
    began = time.monotonic()
    try:
        got = nodes.locate(state)["draft"]
    except Exception as exc:  # noqa: BLE001 - 측정에서는 실패도 한 줄로 남긴다
        return {"name": name, "error": type(exc).__name__, "line_ok": False, "pitfall_ok": False, "fix_ok": False, "one_line": one_line, "seconds": 0}
    fixed = check_judge().judge("python", patched(code, got["line"], got["fixed_line"]), scenario.cases, problem=scenario.text)["status"] == "passed"
    return {"name": name, "line": got["line"], "want": lines, "line_ok": got["line"] in lines, "pitfall": got["pitfall"],
            "pitfall_ok": got["pitfall"] in pitfalls, "fix_ok": fixed, "one_line": one_line, "kind": got["kind"],
            "kind_ok": got["kind"] == rules.kind_hint(report), "seconds": round(time.monotonic() - began, 1)}


def cmd_locate(repeat: int) -> None:
    from .bench import _threads
    from .bench import available

    rows = _threads(locate_one, [bug for bug in BUGS if available(bug[1])] * repeat)
    single = [r for r in rows if r["one_line"]]
    arm = "온톨로지 후보 없음" if os.environ.get("ALGOBLOCK_BENCH_NO_ONTOLOGY") else "온톨로지 후보 있음"
    print(f"테마 debug={pick('debug.locate')} {arm}  줄 {sum(r['line_ok'] for r in rows)}/{len(rows)}"
          f"  함정 {sum(r['pitfall_ok'] for r in rows)}/{len(rows)}  한 줄 고침 통과 {sum(r['fix_ok'] for r in single)}/{len(single)}"
          f"  평균 {sum(r['seconds'] for r in rows) / len(rows):.1f}초")
    for r in rows:
        if not r["line_ok"] or (r["one_line"] and not r["fix_ok"]) or r.get("error"):
            print(f"  {r['name']}: 줄 {r.get('line')}(정답 {r.get('want')}) 함정 {r.get('pitfall')!r} 고침통과 {r['fix_ok']} {r.get('error') or ''}")
