"""화면 서버 확인. 모델을 부르지 않는다(등록 검사, 채점, 언어, 힌트, 해설, 학습 보고서, 처음부터, 파일로 등록).

실행: cd app && uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/test_server.py
기본 문제는 ui/problems에서 지금 검사를 통과해 있는 것(cases.json이 있는 폴더)을 임시 파일로 묶어 쓴다. ui/builtin.json은 건드리지 않는다.
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="algoblock-ui-test-"))
os.environ["ALGOBLOCK_UI_DATA"] = str(TMP / "data")  # 사용자 데이터 폴더를 건드리지 않는다
os.environ["ALGOBLOCK_UI_BUILTIN"] = str(TMP / "builtin.json")
os.environ["ALGOBLOCK_UI_PREPARE"] = "0"
for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_MODEL", "ALGOBLOCK_LLM_PROVIDER", "ALGOBLOCK_EVAL_EXTRA", "ALGOBLOCK_UI_SCENARIOS"):
    os.environ.pop(name, None)  # 키 없이(AI 없이) 도는 것을 본다
sys.path.insert(0, str(HERE))

subprocess.run([sys.executable, str(HERE / "make_builtin.py"), "build", "--no-model", "--no-check", "--no-langs", "--out", os.environ["ALGOBLOCK_UI_BUILTIN"]], check=True, capture_output=True)
ROWS = json.loads(Path(os.environ["ALGOBLOCK_UI_BUILTIN"]).read_text(encoding="utf-8"))
FIRST = next(row for row in ROWS if row["id"] == "hash_1_popular_shelf")  # 본보기 문제: 효율성 케이스가 있다
CODE = FIRST["solutions"]["python"].strip("\n")
LINES = CODE.splitlines()
# 미리 만든 가이드·블록(모델이 만드는 것)을 손으로 넣는다: 블록 둘이 정답 코드를 빠짐없이 나눈다
FIRST["ready"] = {
    "fact": {"spec": "기록을 차례로 보며 값마다 개수를 세고, 개수가 k가 되는 순간의 값을 모은다", "patterns": [], "skills": [], "size": 100000},
    "solution": {"approach": "제목마다 개수를 세며 k가 되는 순간에 담는다.", "steps": ["센다", "담는다"], "code": CODE, "verified": True, "clues": ["'제목이 같으면 같은 책입니다' → 개수를 센다"]},
    "plan": {"strategy": "fresh", "score": None, "algorithm": "hash", "out_of_scope": False, "link": "",
             "blocks": [{"id": "b1", "kind": "loop", "name": "개수 세기", "goal": "제목마다 빌려진 횟수를 센다", "reference": "\n".join(LINES[:5]), "lines": [1, 5], "checks": ["센다"],
                         "hints": ["책마다 몇 번 빌려졌는지 알려면 무엇을 적어 둬야 할까요?", "'제목이 같으면 같은 책입니다'를 보면 무엇을 따로 세야 할까요?", "owl, tide, owl이면 owl은 몇 번 빌려졌나요?"]},
                        {"id": "b2", "kind": "condition", "name": "k번째에 꽂기", "goal": "횟수가 k가 된 순간에 서가에 담는다", "reference": "\n".join(LINES[5:]), "lines": [6, len(LINES)], "checks": ["담는다"],
                         "hints": ["횟수를 올린 뒤에 무엇과 견줘야 할까요?", "'k번째로 빌려지는 바로 그때'는 횟수가 어떤 값일 때일까요?", "k가 2이고 owl이 세 번 빌려지면 몇 번째에 꽂나요?"]}]},
}
JS = ("function solution(loans, k) {\n    const count = {};\n    const shelf = [];\n    for (const title of loans) {\n        count[title] = (count[title] || 0) + 1;\n"
      "        if (count[title] === k) shelf.push(title);\n    }\n    return shelf;\n}\n")
FIRST["solutions"]["javascript"] = JS
FIRST["languages"] = ["python", "javascript"]
Path(os.environ["ALGOBLOCK_UI_BUILTIN"]).write_text(json.dumps(ROWS, ensure_ascii=False), encoding="utf-8")

import server  # noqa: E402
from tutor.common.scope import ALGORITHMS  # noqa: E402
from tutor.common.talk_rules import MANY_ANSWERS  # noqa: E402
from dataclasses import replace  # noqa: E402
from tutor.llm import FakeLlm, use_llm  # noqa: E402
from tutor.main import stale_plan  # noqa: E402

GOOD = {"title": "두 수의 합", "text": "두 수 a, b의 합을 return 하도록 solution 함수를 완성하세요.",
        "cases": [{"input": "[1, 2]", "expected": "3"}, {"input": "", "expected": ""}, {"input": "[5, 5]", "expected": "10"}],
        "again": True}  # 시험은 같은 글을 여러 번 넣는다(같은 글 알림은 아래에서 따로 본다)
PID = FIRST["id"]


def call(path: str, **body):
    return server.handle(path, body)


def refused(body: dict) -> str:
    try:
        server.register(body)
    except server.Refuse as exc:
        return exc.field
    raise AssertionError("거절해야 한다")


def registered() -> None:
    """사용자가 등록한 문제: 검사, 채점, 횟수, 처음부터, 언어마다 코드 기억."""
    assert refused({**GOOD, "title": " "}) == "title"
    assert "제목은 80자까지 적을 수 있어요." in refuses("/api/problems/new", **{**GOOD, "title": "가" * 81})  # 말없이 자르지 않는다
    long_id = server.register({**GOOD, "title": "가" * 80})["id"]  # 등록하면 목록을 통째로 바꿔 끼운다(먼저 읽은 목록에는 없다)
    assert server.PROBLEMS[long_id].title == "가" * 80
    assert refused({**GOOD, "text": ""}) == "text"
    assert refused({**GOOD, "cases": [{"input": "1, 2", "expected": "3"}]}) == "case-input-1"  # 목록이 아니다
    assert refused({**GOOD, "cases": [{"input": "[1]", "expected": "joon"}]}) == "case-expected-1"  # 따옴표 없는 글자
    assert refused({**GOOD, "cases": []}) == "case-input-1"
    for cases, words in (([{"input": "[['mina', 'joon']]", "expected": "1"}], "1번 케이스의 넣을 값을 읽지 못했어요. 문자열은 큰따옴표로 감싸요."),  # 까닭에 맞는 말
                         ([{"input": "[[7, 3],]", "expected": "1"}], "끝에 남은 쉼표를 지워 주세요."), ([{"input": "[1]", "expected": "[1, 2,]"}], "기대 결과를 읽지 못했어요. 끝에 남은 쉼표"),
                         ([{"input": "[1]", "expected": ""}], "1번 케이스의 기대 결과를 적어 주세요."), ([{"input": "1, 2", "expected": "3"}], "대괄호로 감싼 목록")):
        assert words in refuses("/api/problems/new", **{**GOOD, "cases": cases}), cases

    pid = server.register(GOOD)["id"]
    assert [case["id"] for case in server.PROBLEMS[pid].cases] == ["1", "2"]  # 빈 줄은 뺀다
    twice = {key: value for key, value in GOOD.items() if key != "again"}
    assert "같은 글의 문제를 이미 넣었어요" in refuses("/api/problems/new", **{**twice, "text": GOOD["text"] + "  \n"})  # 공백만 다른 같은 글: 준비를 또 하기 전에 알린다
    listed = call("/api/problems")[1]["problems"]
    assert (listed[0]["id"], listed[0]["builtin"], listed[0]["level"]) == (pid, False, 0)  # 최근 등록이 위

    wrong = call("/api/submit", id=pid, code="def solution(a, b):\n    return a - b\n")[1]
    assert not wrong["ok"] and wrong["cases"][0]["got"] == "-1" and wrong["score"] == {"accuracy": [0, 2], "efficiency": [0, 0]}
    right = "def solution(a, b):\n    return a + b\n"
    ran = call("/api/run", id=pid, code=right)[1]
    assert ran["ok"] and len(ran["cases"]) == 2  # 등록한 케이스는 모두 공개 예시다
    assert call("/api/submit", id=pid, code=right)[1]["ok"]
    assert call("/api/debug", id=pid, code=right)[1]["passed"]  # 통과한 코드는 디버깅으로 가지 않는다(모델 0회)
    state = call("/api/state", id=pid, mode="chair")[1]["problem"]
    assert (state["passed"], state["submitted"], state["code"], state["language"]) == (1, 2, right, "python")  # run은 제출로 세지 않는다. 같은 코드는 한 번만 센다
    assert len(state["languages"]) == 7 and state["starter"].startswith("def solution(a, b):") and state["cases"] == {"example": 2, "accuracy": 0, "efficiency": 0}

    # 언어를 바꾸면 쓰던 코드는 그 언어 것으로 남고, 돌아오면 다시 나온다
    java = call("/api/language", id=pid, language="java")[1]["problem"]
    assert (java["language"], java["code"]) == ("java", "")
    call("/api/code", id=pid, code="class Solution {}")
    back = call("/api/language", id=pid, language="python")[1]["problem"]
    assert (back["language"], back["code"]) == ("python", right)
    assert call("/api/language", id=pid, language="java", code="지금 치던 것")[1]["problem"]["code"] == "class Solution {}"
    assert call("/api/language", id=pid, language="python")[1]["problem"]["code"] == "지금 치던 것"
    try:
        call("/api/language", id=pid, language="cobol")
        raise AssertionError("모르는 언어는 거절해야 한다")
    except server.Refuse:
        pass

    call("/api/blocks", id=pid, blocks={"b1": {"code": "x = 1", "by": "me"}})
    call("/api/reset", id=pid)
    state = call("/api/state", id=pid)[1]
    assert (state["problem"]["code"], state["blocks"], state["problem"]["passed"]) == ("", {}, 1)  # 통과 횟수는 남는다
    assert call("/api/feedback/get", id=pid)[0] == 404
    for path in ("/api/hint", "/api/solution"):  # 등록한 문제에는 미리 만든 힌트·해설이 없다
        try:
            call(path, id=pid)
            raise AssertionError(path)
        except server.Refuse as exc:
            assert exc.status == 404


def bundle() -> None:
    """묶인 기본 문제: 주제·단계가 맞고, 실전 신호가 글에 있고, 정답 풀이가 실린 케이스를 통과한다."""
    listed = [row for row in call("/api/problems")[1]["problems"] if row["builtin"]]
    assert len(listed) == len(ROWS) and [row["id"] for row in listed] == [row["id"] for row in ROWS]  # 주제 순서, 단계 순서
    for row in ROWS:
        assert row["theme"] in ALGORITHMS and row["id"].startswith(row["theme"] + "_") and 1 <= row["level"] <= 5, row["id"]
        assert all(signal["phrase"] in row["text"] for signal in row["signals"]), row["id"]
        assert len(row["examples"]) == 3 and set(row["starters"]) == set(server.check_judge().LANGUAGES) and row["languages"][0] == "python", row["id"]
        assert [case["kind"] for case in row["cases"][:3]] == ["example"] * 3, row["id"]
    themes = call("/api/problems")[1]["themes"]
    assert [theme["key"] for theme in themes] == [key for key in ALGORITHMS if any(row["theme"] == key for row in ROWS)]
    if len(ROWS) == 75:  # ui/problems가 다 찼을 때: 주제 15개마다 단계 1~5가 하나씩
        for key in ALGORITHMS:
            assert sorted(row["level"] for row in ROWS if row["theme"] == key) == [1, 2, 3, 4, 5], key
    # 큰 입력(효율성 케이스)은 채점할 때 다시 만든다: 실린 정답 풀이가 얼려 둔 기대 결과와 맞아야 한다(난수 계산이 바뀌면 여기서 걸린다)
    for row in [FIRST, *[row for row in ROWS if row["large"] and row is not FIRST][:2]]:
        report = server.grade(server.PROBLEMS[row["id"]], "python", row["solutions"]["python"])
        assert report["status"] == "passed" and sum(case["kind"] == "efficiency" for case in report["cases"]) >= 1, (row["id"], report["status"])


def limits() -> None:
    """효율성 케이스의 제한: 문제의 limits[언어]가 있으면 그 값, 없으면 casegen.LIMIT. 정확성 케이스에는 주지 않는다. 화면에 넘기는 limit도 같은 값이다."""
    from casegen import LIMIT, limit_of

    assert [limit_of("java", 0.148), limit_of("java", 0.05), limit_of("python", 1.7), limit_of("cpp", 0.9)] == [1.5, 1.0, 10.0, 2.0]
    seen = []

    def judge(language, code, cases, **_):
        seen.append({case["id"]: case.get("timeout") for case in cases})
        return {"status": "passed", "cases": [{"id": case["id"], "expected": case["expected"], "status": "passed", "time_ms": 1300, "near": True} for case in cases]}

    p, kinds = server.PROBLEMS[PID], {case["id"]: case["kind"] for case in FIRST["cases"]}
    with patch.object(server, "check_judge", lambda: SimpleNamespace(judge=judge)), patch.dict(server.BUILTIN[PID]):
        server.BUILTIN[PID]["limits"] = {"python": 1.5}
        shown = server.grade(p, "python", CODE)["cases"]
        server.grade(p, "java", CODE)
        del server.BUILTIN[PID]["limits"]
        server.grade(p, "python", CODE)
    expect = [1.5, LIMIT["java"], LIMIT["python"]]  # 문제의 값, 그 언어의 값이 없으면 LIMIT, limits가 없으면 LIMIT
    for timeouts, limit in zip(seen, expect):
        assert {timeouts[cid] for cid, kind in kinds.items() if kind == "efficiency"} == {limit} and {timeouts[cid] for cid, kind in kinds.items() if kind != "efficiency"} == {None}, timeouts
    assert {case["limit"] for case in shown if case["kind"] == "efficiency"} == {1.5}  # 화면의 '제한 시간에 가까워요(a초 / b초)'
    stops = []  # 블록 코드 확인(quick)은 시간 초과 한 번에 남은 케이스를 돌리지 않는다. 제출·예시 실행은 채점기 기본값(끝나지 않는 반복에 30초)
    with patch.object(server, "check_judge", lambda: SimpleNamespace(judge=lambda *a, **k: stops.append(k.get("stop_after")) or judge(*a[:3]))):
        server.verify(PID, CODE, quick=True)
        server.verify(PID, CODE)
    assert stops == [1, None], stops
    # 블록 코드 확인은 제한 시간이 없는 케이스에 max(2초, 그 언어의 효율성 제한)을 준다(끝나지 않는 반복이 10초를 기다렸다). 제출은 그대로
    seen.clear()
    with patch.object(server, "check_judge", lambda: SimpleNamespace(judge=judge)), patch.dict(server.BUILTIN[PID]):
        for limit in (1.5, 3.0):
            server.BUILTIN[PID]["limits"] = {"python": limit}
            server.verify(PID, CODE, quick=True)
        server.verify(PID, CODE)
        del server.BUILTIN[PID]["limits"]
        server.verify(PID, CODE, quick=True)
    assert [set(timeouts.values()) for timeouts in seen[:2]] == [{2.0}, {3.0}], seen[:2]
    assert {seen[2][cid] for cid, kind in kinds.items() if kind != "efficiency"} == {None} and set(seen[3].values()) == {None}, seen[2:]


def builtin(fake) -> None:
    """기본 문제 하나를 AI 없이 끝까지: 열기, 예시 실행, 제출, 숨김 규칙, 힌트, 해설, 언어 바꾸기."""
    opened = call("/api/state", id=PID, mode="chair", open=True)[1]
    problem = opened["problem"]
    assert (problem["builtin"], problem["theme"], problem["theme_name"], problem["level"], problem["languages"]) == (True, "hash", "해시", 1, ["python", "javascript"])
    assert problem["starter"].startswith("def solution(loans, k)") and problem["code"] == "" and len(problem["examples"]) == 3 and problem["examples"][0]["note"]
    assert problem["cases"]["example"] == 3 and problem["cases"]["accuracy"] >= 12 and problem["cases"]["efficiency"] == 2
    assert problem["study"] == {"hints_seen": 0, "hints_total": 6, "solution_seen": False, "solution_open": False, "has_guide": True}
    assert len(opened["session"]["blocks"]) == 2  # 미리 만든 계획으로 바로 시작한다
    first = call("/api/turn", id=PID, mode="chair", event="start")[1]
    assert first["messages"][0]["text"] == FIRST["ready"]["plan"]["blocks"][0]["hints"][0]
    hidden = next(case["input"] for case in FIRST["cases"] if case["kind"] == "accuracy" and len(case["input"]) > 12)
    for body in (opened, first, call("/api/problems")[1]):  # 정답 코드와 숨긴 케이스의 입력은 나가지 않는다
        dumped = json.dumps(body, ensure_ascii=False)
        assert "count.get" not in dumped and hidden not in dumped and "prefix_count" not in dumped

    ran = call("/api/run", id=PID, code=problem["starter"])[1]
    assert not ran["ok"] and [case["kind"] for case in ran["cases"]] == ["example"] * 3 and ran["cases"][0]["expected"] == '["tide", "owl"]'
    assert call("/api/state", id=PID)[1]["problem"]["submitted"] == 0  # 예시 실행은 제출이 아니다

    # 직접 넣은 값으로 한 번 실행: 판정 없이 돌려준 값만. 찍은 것은 따로. 모양이 틀린 입력은 400. 제출로 세지 않는다
    own = call("/api/run", id=PID, code=CODE, input=' [["a", "b", "a"], 2] ')[1]
    assert (own["status"], own["got"], own["input"], own["stdout"], own["error"]) == ("ran", '["a"]', '[["a", "b", "a"], 2]', "", ""), own
    assert "expected" not in own and "ok" not in own  # 판정하지 않는다(제출이 아니다)
    assert (own["reference"], own["same"]) == ('["a"]', True)  # 기본 문제는 정답 풀이의 결과를 같이 보여 준다
    printed = call("/api/run", id=PID, code="def solution(loans, k):\n    print('hi')\n    return loans\n", input='[["a"], 2]')[1]
    assert (printed["status"], printed["got"], printed["stdout"], printed["reference"], printed["same"]) == ("ran", '["a"]', "hi", "[]", False)
    broken = call("/api/run", id=PID, code="def solution(loans, k):\n    x = 1\n    return x / 0\n", input='[["a"], 2]')[1]
    assert broken["status"] == "runtime_error" and broken["error"].startswith("ZeroDivisionError") and broken["got"] == "" and "0으로 나눴어요" in broken["hint"]
    assert broken["reference"] == "[]" and "same" not in broken  # 내 코드가 돌지 못했으면 견주지 않는다
    with patch.object(server, "check_judge", lambda: SimpleNamespace(judge=lambda *a, **k: {"status": "timeout", "cases": [{"status": "timeout", "stdout": ""}]}, common=None)):
        assert server.reference(FIRST, '[["a"], 2]', "[]") == {"reference_note": server.OUT_OF_RANGE}  # 정답 풀이가 시간을 넘기면 제한사항 밖의 입력이다
    for bad, words in (("level", "대괄호로 감싼 목록"), ('{"s": "a"}', "대괄호로 감싼 목록"), ("[NaN]", "대괄호로 감싼 목록"),
                       ('["a", "b"]', f"입력 모양과 달라요. 예: {FIRST['examples'][0]['input']}"), ("[['a'], 2]", "큰따옴표로 감싸요"), ('[["a",], 2]', "끝에 남은 쉼표"),
                       ("[1]", "입력 모양"), ("[" + '"a",' * 7000 + "]", "20,000자"), (["a"], "20,000자")):
        assert words in refuses("/api/run", id=PID, code=CODE, input=bad), bad
    assert call("/api/state", id=PID)[1]["problem"]["submitted"] == 0

    try:  # 통과 전에는 해설이 잠겨 있다
        assert call("/api/solution", id=PID)[0] == 409
    except server.Refuse:
        raise AssertionError("잠김은 409로 알린다") from None
    slow = ("def solution(loans, k):\n    shelf = []\n    for i in range(len(loans)):\n        n = 0\n        for j in range(i + 1):\n            if loans[j] == loans[i]:\n"
            "                n += 1\n        if n == k:\n            shelf.append(loans[i])\n    return shelf\n")
    wrong = call("/api/submit", id=PID, code="def solution(loans, k):\n    return sorted(set(t for t in loans if loans.count(t) >= k))\n")[1]
    assert not wrong["ok"] and wrong["score"]["accuracy"][0] < wrong["score"]["accuracy"][1]
    assert any(case["kind"] == "accuracy" and case["status"] != "passed" for case in wrong["cases"])
    for case in wrong["cases"]:  # 숨은 테스트는 틀려도 입력·기대값·내 결과를 싣지 않는다(공개 예시만). 큰 입력의 크기도 싣지 않는다
        assert ("input" in case) == ("expected" in case) == ("got" in case) == (case["kind"] == "example") and "size" not in case, case
    timed = call("/api/submit", id=PID, code=slow)[1]  # 답은 맞지만 느린 풀이: 정확성은 다 맞고 효율성에서 시간 초과
    assert timed["status"] == "timeout" and timed["score"]["accuracy"][0] == timed["score"]["accuracy"][1] and timed["score"]["efficiency"][0] < 2
    debug = call("/api/debug", id=PID, code=slow)[1]
    assert debug["efficiency_only"] and not debug["passed"]  # 틀린 줄을 찾을 일이 아니다(모델 0회)

    assert call("/api/hint", id=PID, peek=True)[1] == {"seen": 0, "total": 6, "done": False, "shown": []}  # 들여다보기만 하면 새 힌트가 열리지 않는다
    hints = [call("/api/hint", id=PID)[1] for _ in range(7)]
    assert len(call("/api/hint", id=PID, peek=True)[1]["shown"]) == 6
    assert [(h["block"], h["step"]) for h in hints] == [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (2, 3)]
    assert hints[0]["hint"] == FIRST["ready"]["plan"]["blocks"][0]["hints"][0] and [h["done"] for h in hints[4:]] == [False, True, True] and len(hints[2]["shown"]) == 3
    # 블록 이름(답의 일부)은 그 블록의 힌트를 모두 본 뒤에만 서버가 보낸다. 종류는 늘 보낸다
    assert [h.get("name") for h in hints[:6]] == [None, None, "개수 세기", None, None, "k번째에 꽂기"] and [h["kind"] for h in hints] == ["loop"] * 3 + ["condition"] * 4
    assert [h.get("name") for h in hints[3]["shown"]] == ["개수 세기"] * 3 + [None] and "k번째에 꽂기" not in json.dumps(hints[4], ensure_ascii=False)
    forced = call("/api/solution", id=PID, force=True)[1]
    assert forced["code"].strip() == CODE and forced["language"] == "python" and forced["clues"] and forced["signals"] == FIRST["signals"]
    assert forced["next"] is None or forced["next"]["id"].startswith("hash_")
    # 다음 문제는 그 주제에서 아직 통과하지 않은 가장 낮은 단계(이미 통과한 2단계를 건너뛴다). 다 통과했으면 없다(화면이 홈의 추천을 쓴다)
    assert server.next_problem("hash_3_bead_bracelets", {"hash_2_steady_climbers"})["id"] == "hash_1_popular_shelf"
    assert server.next_problem("hash_1_popular_shelf", {"hash_2_steady_climbers"})["id"] == "hash_3_bead_bracelets"
    assert server.next_problem("hash_1_popular_shelf", {r for r in server.BUILTIN if r.startswith("hash_")}) is None
    passed = call("/api/submit", id=PID, code=CODE)[1]
    assert passed["ok"] and passed["score"]["efficiency"] == [2, 2] and all("input" not in case for case in passed["cases"] if case["kind"] != "example")
    study = call("/api/state", id=PID)[1]["problem"]["study"]
    assert study == {"hints_seen": 6, "hints_total": 6, "solution_seen": True, "solution_open": True, "has_guide": True}
    with server.tutor() as t:
        assert t.store.study(PID)["solution_before_pass"] and [sub["status"] for sub in t.store.submissions() if sub["problem_id"] == PID] == ["failed", "timeout", "passed"]

    # 처음부터 해도 같은 블록으로 다시 바로 시작된다(정석 계획은 남기고 첫 블록으로만 돌린다)
    call("/api/reset", id=PID)
    assert call("/api/turn", id=PID, mode="chair", event="start")[1]["messages"][0]["text"] == first["messages"][0]["text"]

    # 언어를 바꾸면 그 언어의 시작 코드가 오고, 블록 계획은 지워진다(그 언어의 정답 풀이로 다시 짠다). 파이썬으로 돌아오면 미리 만든 계획이 다시 온다
    js = call("/api/language", id=PID, language="javascript")[1]
    assert js["problem"]["language"] == "javascript" and js["problem"]["starter"].startswith("function solution(loans, k)") and js["session"]["blocks"] == []
    assert server.given(PID, "javascript")["code"] == JS and server.given(PID, "javascript")["approach"] and server.given(PID, "go") is None
    if server.check_judge().judge("javascript", JS, [{"id": "1", "input": "[[\"a\"], 2]", "expected": "[]"}], mode="function")["status"] != "toolchain_missing":
        assert call("/api/submit", id=PID, code=JS)[1]["ok"]
        assert call("/api/solution", id=PID)[1]["language"] == "javascript"
    else:
        assert call("/api/submit", id=PID, code=JS)[1]["status"] == "toolchain_missing"
    assert len(call("/api/language", id=PID, language="python")[1]["session"]["blocks"]) == 2
    with server.tutor() as t:  # 돌아온 계획은 그 언어로 쓰던 코드가 있고 대화가 지워졌어도 낡았다고 다시 짜지 않는다
        t.store.update_code(PID, CODE)
        back = t.store.load(PID)
        assert back.plan.settled and not stale_plan(back) and stale_plan(replace(back, plan=replace(back.plan, settled=False)))
        t.store.update_code(PID, "")
    assert not fake.calls, fake.calls  # 여기까지 모델을 한 번도 부르지 않았다


def report() -> None:
    """학습 보고서의 수치가 넣은 제출 기록과 맞는다. 출석은 /api/problems가 오늘을 한 번만 찍는다."""
    call("/api/problems")
    body = call("/api/report")[1]
    assert body["attendance"]["days"] == 1 and len(body["attendance"]["recent"]) == 14 and body["attendance"]["recent"][-1] is True and not any(body["attendance"]["recent"][:-1])
    hash_ = next(theme for theme in body["themes"] if theme["key"] == "hash")
    assert (hash_["solved"], hash_["level_reached"], hash_["first_try"], hash_["solution_before_pass"], hash_["hints"]) == (1, 1, 0, 1, 6), hash_
    assert hash_["fails"] == {"failed": 1, "runtime_error": 0, "timeout": 1, "compile_error": 0} and hash_["submissions"] >= 3 and hash_["state"] in ("progress", "weak")
    assert body["summary"]["solved"] == 1 and body["summary"]["total"] == len(ROWS) and body["summary"]["languages"]["python"] >= 5
    assert body["recent"][0]["id"] == PID and len(body["recent"]) <= 10
    assert [group["key"] for group in body["signals"]] == ["hash"] and body["signals"][0]["items"][0]["title"] == FIRST["title"]  # 푼 문제의 신호만
    assert 1 <= len(body["next"]) <= 5 and all(row["id"] != PID for row in body["next"])
    others = [theme for theme in body["themes"] if theme["key"] != "hash"]
    assert all(theme["state"] == "new" for theme in others)
    # 약점 규칙: 한 주제에서 시간 초과가 두 번 나오면 약한 주제다
    with server.tutor() as t:
        other = next(row for row in ROWS if row["theme"] != "hash")
        t.store.put_problem(other["id"], "python", other["text"], title=other["title"])
        for n in range(2):
            t.store.add_submission(other["id"], f"느린 코드 {n}", False, status="timeout")
    weak = call("/api/report")[1]["weaknesses"]
    assert weak and weak[0]["key"] == other["theme"] and "시간 초과" in weak[0]["why"] and weak[0]["next"]["id"].startswith(other["theme"])
    # 한 문제에서 여러 번 틀리고 끝내 푼 것만으로는 약한 주제가 아니다
    with server.tutor() as t:
        third = next(row for row in ROWS if row["theme"] not in ("hash", other["theme"]))
        t.store.put_problem(third["id"], "python", third["text"], title=third["title"])
        for n in range(4):
            t.store.add_submission(third["id"], f"틀린 코드 {n}", False, status="failed")
        t.store.add_submission(third["id"], "맞은 코드", True, status="passed")
    assert next(theme for theme in call("/api/report")[1]["themes"] if theme["key"] == third["theme"])["state"] == "progress"
    # 함수 이름이 틀린 제출(entry_missing)·형을 못 읽는 제출은 컴파일 오류로, 판정 못 한 제출(undecided)은 오답으로 센다
    with server.tutor() as t:
        for status in ("entry_missing", "unsupported_signature", "undecided"):
            t.store.add_submission(third["id"], f"모양이 틀린 코드 {status}", False, status=status)
    assert next(theme for theme in call("/api/report")[1]["themes"] if theme["key"] == third["theme"])["fails"] == {"failed": 5, "runtime_error": 0, "timeout": 0, "compile_error": 2}


def home() -> None:
    """이어서 풀기와 다음 문제: 다음 단계는 통과한 가장 높은 단계 위에서, 쓰던 문제가 먼저, 약한 주제는 해설을 먼저 본 문제부터. 보고서는 등록한 문제의 제출도 센다."""
    ladder = [{"id": key, "level": n} for n, key in enumerate("abcde", 1)]
    assert [(server.next_up(ladder, set(done)) or {}).get("id") for done in ("ce", "abcde", "e", "")] == ["d", None, "a", "a"]
    fresh, plain = [row for row in ROWS if row["theme"] == ROWS[-1]["theme"]][:2]  # 아직 손대지 않은 주제
    call("/api/code", id=fresh["id"], code="def solution(s):\n    stack = []\n")  # 제출 없이 코드만 썼다
    call("/api/code", id=plain["id"], code=plain["starters"]["python"] + "\n")  # 시작 코드 그대로는 손댄 것이 아니다
    listed = {row["id"]: row for row in call("/api/problems")[1]["problems"]}
    assert (listed[fresh["id"]]["touched"], listed[plain["id"]]["touched"], listed[PID]["touched"]) == (True, False, False)
    weak = next(row for row in call("/api/report")[1]["themes"] if row["state"] == "weak" and row["key"] != "hash")
    sent = [sub["id"] for sub in call("/api/report")[1]["recent"]]
    stuck = next(row for row in ROWS if row["theme"] == weak["key"] and row["id"] in sent)
    again = next(row for row in ROWS if row["theme"] == weak["key"] and row["id"] != stuck["id"])
    with server.tutor() as t:
        t.store.put_problem(again["id"], "python", again["text"], title=again["title"])
        t.store.set_study(again["id"], solution_at=server.now(), solution_before_pass=True)
    body = call("/api/report")[1]
    assert (body["next"][0]["id"], body["next"][0]["why"]) == (fresh["id"], "쓰던 문제예요.")  # 제출 없이 코드만 쓴 것이라도 가장 최근에 손댄 문제
    assert plain["id"] not in server.read_json(server.TOUCHED_FILE, {})  # 시작 코드 그대로 저장한 것은 손댄 것이 아니다
    call("/api/code", id=stuck["id"], code="def solution(x):\n    return 0\n")  # 다시 손대면 그 문제가 먼저
    body = call("/api/report")[1]
    assert (body["next"][0]["id"], body["next"][0]["why"]) == (stuck["id"], "쓰던 문제예요.")
    assert {"id": again["id"], "why": "해설을 먼저 본 문제예요. 힌트 없이 다시 풀어 보세요."}.items() <= next(row for row in body["next"] if row["id"] == again["id"]).items()
    assert next(row for row in body["weaknesses"] if row["key"] == weak["key"])["next"]["id"] == again["id"]
    # 등록한 문제의 제출도 '통과하지 못한 제출'에 들고, 등록한 문제의 통과 수를 따로 준다
    before = body["summary"]
    pid = server.register(GOOD)["id"]
    gone = server.register(GOOD)["id"]
    call("/api/code", id=gone, code="def solution(a, b):\n    return 0\n")
    assert gone in server.read_json(server.TOUCHED_FILE, {}) and call("/api/report")[1]["next"][0]["id"] == gone
    call("/api/problems/delete", id=gone)
    assert gone not in server.read_json(server.TOUCHED_FILE, {})  # 지우면 손댄 시각도 지운다
    with server.tutor() as t:
        t.store.add_submission(pid, "fn main() {}", False, language="rust", status="compile_error")
    after = call("/api/report")[1]["summary"]
    assert after["fails"]["compile_error"] == before["fails"]["compile_error"] + 1 and sum(after["fails"].values()) == sum(before["fails"].values()) + 1
    assert after["own"] == {"solved": before["own"]["solved"], "total": before["own"]["total"] + 1} and before["own"]["solved"] >= 1
    assert sum(sum(theme["fails"].values()) for theme in call("/api/report")[1]["themes"]) == sum(sum(theme["fails"].values()) for theme in body["themes"])  # 주제별은 기본 문제만


def own_theme() -> None:
    """등록 문제의 주제: 저장, 목록 꼬리표, 계획의 알고리즘은 보여 주기만, 보고서의 제출·실패 수와 약점 판정에 더한다(단계·문제 수는 기본 문제만)."""
    assert [row["key"] for row in call("/api/accounts")[1]["topics"]] == list(ALGORITHMS)
    assert "고를 수 없는 주제예요." in refuses("/api/problems/new", **GOOD, theme="cobol")
    before = {row["key"]: row for row in call("/api/report")[1]["themes"]}
    key = next(k for k, row in before.items() if row["state"] == "new")
    pid = server.register({**GOOD, "theme": key})["id"]
    plain = server.register(GOOD)["id"]  # 주제 없는 문제
    listed = {row["id"]: row for row in call("/api/problems")[1]["problems"]}
    assert (listed[pid]["theme_name"], listed[plain]["theme_name"], call("/api/state", id=pid)[1]["problem"]["theme"]) == (server.theme_name(key), "", key)
    with server.tutor() as t:
        for n in range(2):
            t.store.add_submission(pid, f"느린 코드 {n}", False, status="timeout")
        for n in range(3):
            t.store.add_submission(plain, f"틀린 코드 {n}", False, status="timeout")
        t.adopt(plain, FIRST["ready"])  # 튜터가 짠 계획의 알고리즘(hash)은 주제를 정하지 않은 문제에 보여 주기만 한다
    body = call("/api/report")[1]
    row = next(row for row in body["themes"] if row["key"] == key)
    assert (row["state"], row["submissions"], row["fails"]["timeout"], row["solved"], row["total"]) == ("weak", 2, 2, 0, before[key]["total"])
    assert row["why"].startswith("시간 초과가 2번") and any(weak["key"] == key for weak in body["weaknesses"])
    assert {k: (r["submissions"], r["fails"]) for k, r in ((r["key"], r) for r in body["themes"]) if k != key} == {k: (r["submissions"], r["fails"]) for k, r in before.items() if k != key}  # 주제 없는 문제는 주제별 계산에 없다
    assert next(row for row in call("/api/problems")[1]["problems"] if row["id"] == plain)["theme_name"] == "해시" and call("/api/state", id=plain)[1]["problem"]["theme"] == ""
    assert call("/api/state", id=plain)[1]["problem"]["theme_name"] == "해시"  # 문제 화면의 배지도 목록과 같이 보인다
    key2 = next(k for k, row in before.items() if row["state"] == "new" and k != key)  # 주제 줄: 기본 문제의 통과와 등록한 문제의 통과를 나눠 말한다
    solved = server.register({**GOOD, "theme": key2})["id"]
    with server.tutor() as t:
        t.store.add_submission(solved, "틀린 코드", False, status="failed")
        t.store.add_submission(solved, "맞은 코드", True, status="passed")
    row = next(row for row in call("/api/report")[1]["themes"] if row["key"] == key2)
    assert row["state"] == "progress" and row["why"].startswith(f"기본 문제 {before[key2]['total']}문제 중 0문제를 풀었어요. 등록한 문제 1개를 풀었어요."), row
    body = call("/api/report")[1]  # 등록 문제만 푼 주제는 '이어서 풀기'가 아니다(풀고 있는 주제는 기본 문제의 기록으로만). 까닭에 주제·단계를 되풀이하지 않는다
    assert all(n["why"] == "새 주제 시작" for n in body["next"] if n["theme_name"] == server.theme_name(key2)), body["next"]
    assert not any(n["why"].startswith(("이어서 풀기:", "새 주제 시작:", "한 단계 더:")) for n in body["next"]), body["next"]
    call("/api/problems/edit", id=plain, **GOOD, theme=key)  # 고른 주제가 이긴다
    assert next(row for row in call("/api/problems")[1]["problems"] if row["id"] == plain)["theme_name"] == server.theme_name(key)
    call("/api/problems/edit", id=plain, **GOOD)  # theme를 보내지 않으면 그대로
    assert server.PROBLEMS[plain].theme == key
    call("/api/problems/edit", id=plain, **GOOD, theme="")
    assert server.PROBLEMS[plain].theme == ""


def debug_pass() -> None:
    """틀린 곳 같이 찾기 중 고친 코드가 통과하면(엔진·모델 0회) 내 말과 맺음말이 디버그 대화에 남는다. 말 없이 통과하면 맺음말만."""
    pid = server.register(GOOD)["id"]
    call("/api/submit", id=pid, code="def solution(a, b):\n    return a - b\n")
    got = call("/api/debug", id=pid, code="def solution(a, b):\n    return a + b\n", text="빼기를 더하기로 고쳤어요")[1]
    assert got["passed"] and [(m["role"], m["text"]) for m in got["messages"]] == [("user", "빼기를 더하기로 고쳤어요"), ("service", server.DEBUG_DONE)]
    assert [(m["role"], m["text"]) for m in call("/api/state", id=pid)[1]["session"]["debug"]] == [("user", "빼기를 더하기로 고쳤어요"), ("service", server.DEBUG_DONE)]
    other = server.register(GOOD)["id"]
    assert [m["text"] for m in call("/api/debug", id=other, code="def solution(a, b):\n    return b + a\n")[1]["messages"]] == [server.DEBUG_DONE]
    # 디버그 안에서 다시 채점해도 제출로 남기지 않는다(예시 실행 뒤에 열어도 제출 수가 늘지 않는다). 위에서 제출은 틀린 것 한 번뿐이다
    state = call("/api/state", id=pid)[1]["problem"]
    assert got["judged"]["unsaved"] and got["judged"]["ok"] and (state["submitted"], state["passed"]) == (1, 0), (state["submitted"], state["passed"])


def own_way_flow() -> None:
    """'끝까지 내 방식으로 쓰기'(모델·실행 0회): 지금 블록은 넘어가기와 같게 확인 전, 남은 블록을 모두 열고 표시가 남는다(다시 열어도).
    통과(Y)를 새로 만들지 않는다. '튜터 차례로 돌아가기' 뒤에는 블록 코드 확인이 다시 돈다. 초기화하면 표시도 지운다."""
    call("/api/reset", id=PID)
    call("/api/turn", id=PID, mode="guide", event="start")
    call("/api/turn", id=PID, mode="guide", event="block_filled", block_id="b1", code="\n".join(LINES[:5]), skip=True, quiet=True, own_way=True)
    state = call("/api/state", id=PID, mode="guide")[1]
    blocks = state["session"]["blocks"]
    assert state["own_way"] and state["session"]["open_count"] == len(blocks) == 2, state["session"]["open_count"]
    assert [b.get("verdict") for b in blocks] == ["?", None], [b.get("verdict") for b in blocks]
    assert call("/api/own_way", id=PID, on=True)[1] == {"own_way": True}  # 켜진 것을 다시 켜도 그대로다(켜는 것은 넘어가기 요청만)
    assert call("/api/own_way", id=PID, on=False)[1] == {"own_way": False} and not call("/api/state", id=PID)[1]["own_way"]
    assert call("/api/own_way", id=PID, on=True)[1] == {"own_way": False}  # 꺼진 것을 이 길로 켜지 않는다
    call("/api/turn", id=PID, mode="guide", event="block_filled", block_id="b2", code="\n".join(LINES[5:]))  # 돌아간 뒤: 블록 코드 확인이 다시 돈다
    after = call("/api/state", id=PID, mode="guide")[1]["session"]["blocks"]
    assert [b.get("verdict") for b in after] == ["?", "Y"], after  # 확인한 블록 2만 통과(넘어간 블록 1은 확인 전 그대로)
    call("/api/turn", id=PID, mode="guide", event="block_filled", block_id="b2", code="\n".join(LINES[5:]), skip=True, quiet=True, own_way=True)
    assert call("/api/state", id=PID)[1]["own_way"]
    call("/api/reset", id=PID)
    assert not call("/api/state", id=PID)[1]["own_way"]


def chair_found() -> None:
    """의자에서 찾은 블록의 블록 코드 확인(모델 0회): 맞다고만 하고 진행은 그대로, 그 말은 그 블록을 겨눈다. 가이드는 지금 블록만.
    계획 코드와 글자 그대로 같으면 실행 없이, 틀 줄을 빼고 적으면 실행해 본다(그 문제의 예시만 있는 등록 문제라 그렇다고 말한다)."""
    pid = server.register({"title": FIRST["title"], "text": FIRST["text"], "cases": [{"input": e["input"], "expected": e["expected"]} for e in FIRST["examples"]]})["id"]
    with server.tutor() as t:
        t.adopt(pid, FIRST["ready"])
    call("/api/turn", id=pid, mode="chair", event="start")
    assert call("/api/fill", id=pid, block_id="b1")[1]["open_count"] == 2  # 채우기로 1번 블록을 찾았다
    status, body = call("/api/turn", id=pid, mode="chair", event="block_filled", block_id="b1", code="\n".join(LINES[:5]))
    assert status == 200 and body["open_count"] == 2 and body["messages"][-1]["text"].startswith("통과예요")
    assert [(m["role"], m["block_index"]) for m in body["messages"][-2:]] == [("user", 0), ("service", 0)]
    indented = "\n".join(LINES[1:5])  # 첫 줄 앞 공백이 저장까지 남는다(저장하며 첫 줄 들여쓰기를 잃어 다음 확인에서 평평해졌다)
    said = call("/api/turn", id=pid, mode="chair", event="block_filled", block_id="b1", code="\n" + indented + "  \n")[1]["messages"][-1]["text"]
    assert said == "공개 예시로만 확인했어요. 통과예요. 이 블록의 코드는 할 일을 해내요.", said
    with server.tutor() as t:
        assert t.store.load(pid).block_states["b1"].code == indented, t.store.load(pid).block_states["b1"].code
    status, body = call("/api/turn", id=pid, mode="guide", event="block_filled", block_id="b1", code="\n".join(LINES[:5]))  # 가이드도 앞 블록을 고쳐 다시 확인한다
    assert status == 200 and body["open_count"] == 2, body


def language_memory() -> None:
    """마지막으로 고른 언어를 기억한다: 처음 여는 기본 문제는 그 언어로(지원할 때), 이미 연 문제는 그 문제의 언어 그대로."""
    with server.tutor() as t:
        unopened = [row for row in ROWS if t.store.load(row["id"]) is None]
        opened = next(row for row in ROWS if row["id"] != PID and t.store.load(row["id"]) is not None)
    call("/api/language", id=PID, language="javascript")
    assert call("/api/accounts")[1]["language"] == "javascript"
    for row in unopened[:3]:
        want = "javascript" if "javascript" in row["languages"] else "python"
        assert call("/api/state", id=row["id"])[1]["problem"]["language"] == want, row["id"]
    assert call("/api/state", id=opened["id"])[1]["problem"]["language"] == "python"
    call("/api/language", id=PID, language="python")
    assert call("/api/accounts")[1]["language"] == "python"


def no_tool() -> None:
    """언어 도구가 없어 채점하지 못한 것은 제출로 세지 않는다(새 제출도, 예전에 저장된 기록도)."""
    before = (next(row for row in call("/api/problems")[1]["problems"] if row["id"] == PID)["submitted"], call("/api/report")[1]["summary"]["submissions"])
    grade = server.grade
    server.grade = lambda *args, **kwargs: {"status": "toolchain_missing", "reason": "go 없음", "cases": [], "compile": ""}
    try:
        assert call("/api/submit", id=PID, code="func solution() {}")[1]["status"] == "toolchain_missing"
    finally:
        server.grade = grade
    with server.tutor() as t:
        t.store.add_submission(PID, "예전 기록", False, language="go", status="toolchain_missing")
    after = (next(row for row in call("/api/problems")[1]["problems"] if row["id"] == PID)["submitted"], call("/api/report")[1]["summary"]["submissions"])
    assert after == before, (before, after)


def results() -> None:
    """채점 결과 모양. 채점기의 새 필드(line, near, skipped, compile_line)는 grade를 바꿔 끼워 흉내 낸다.
    줄 번호, 숨은 테스트는 예외 이름과 줄 번호만, 한 줄 풀이, 돌리지 않은 케이스, 제한 시간에 가까운 통과, 같은 코드 다시 내기, 직접 입력의 모양 검사."""
    pid = server.register(GOOD)["id"]
    hidden_error = 'Exception in thread "main" java.lang.ArrayIndexOutOfBoundsException: Index 100000 out of bounds for length 100000\n\tat Solution.solution(Solution.java:4)'
    case = {"input": "[1, 2]", "expected": "3", "got": "", "error": "", "ms": 5, "line": None, "near": False, "limit": None}
    fake = {"status": "runtime_error", "reason": "", "compile": "", "compile_line": None, "language": "java", "cases": [
        {**case, "id": "1", "kind": "example", "status": "runtime_error", "error": 'Exception in thread "main" java.lang.NullPointerException: x\n\tat FunctionRunner.main(FunctionRunner.java:9)', "line": 3},
        {**case, "id": "2", "kind": "accuracy", "status": "runtime_error", "error": hidden_error, "line": 4},
        {**case, "id": "3", "kind": "accuracy", "status": "timeout", "ms": 10000},
        {**case, "id": "4", "kind": "accuracy", "status": "skipped", "ms": 0, "error": "앞선 테스트에서 시간 초과가 이어져 돌리지 않았어요."},
        {**case, "id": "5", "kind": "efficiency", "status": "passed", "ms": 3900, "near": True, "limit": 4},
        {**case, "id": "6", "kind": "efficiency", "status": "runtime_error", "error": hidden_error}]}
    grade = server.grade
    server.grade = lambda *args, **kwargs: fake
    try:
        body = call("/api/submit", id=pid, code="class Solution {}")[1]
        again = call("/api/submit", id=pid, code=" class Solution {} \n")[1]  # 같은 언어·코드·결과는 다시 남기지 않는다
        call("/api/language", id=pid, language="java")
        other = call("/api/submit", id=pid, code="class Solution {}")[1]  # 언어가 다르면 남긴다
        fake["status"] = "failed"
        changed = call("/api/submit", id=pid, code="class Solution {}")[1]  # 결과가 달라졌으면 남긴다
        compiled = server.result_body({**fake, "status": "compile_error", "cases": [], "compile": "Solution.java:6: error: ';' expected", "compile_line": 6})
    finally:
        server.grade = grade
    one, two, timed, skipped, near, eff = body["cases"]
    assert (one["error"], one["line"], one["input"]) == ('Exception in thread "main" java.lang.NullPointerException: x', 3, "[1, 2]") and one["hint"].startswith("null인 값")
    assert (two["error"], two["line"], "input" in two) == ("ArrayIndexOutOfBoundsException", 4, False) and "100000" not in json.dumps(body)  # 숨은 테스트는 예외 이름만
    assert eff["error"] == "ArrayIndexOutOfBoundsException" and "line" not in eff and two["hint"].startswith("배열의 범위")
    assert skipped["status"] == "skipped" and "error" not in skipped and timed["status"] == "timeout" and body["score"] == {"accuracy": [0, 4], "efficiency": [1, 2]}
    assert (near["near"], near["limit"]) == (True, 4) and "near" not in eff
    assert [case["status"] for case in server.tutor_view(fake)["cases"]][2:4] == ["timeout", "timeout"]  # 엔진은 돌리지 않음을 모른다
    assert [case["kind"] for case in server.tutor_view(fake)["cases"]] == ["example", "accuracy", "accuracy", "accuracy", "efficiency", "efficiency"]  # 엔진이 공개 예시를 가른다
    assert (server.tutor_view(fake)["cases"][0]["line"], server.tutor_view({**fake, "status": "compile_error", "compile_line": 6})["compile_line"]) == (3, 6)  # 오류의 줄을 엔진이 안다(내 블록의 줄인지 가른다)
    assert (body["repeat"], again["repeat"], other["repeat"], changed["repeat"]) == (False, True, False, False)
    with server.tutor() as t:
        assert [(sub["language"], sub["status"]) for sub in t.store.submissions() if sub["problem_id"] == pid] == [("python", "runtime_error"), ("java", "runtime_error"), ("java", "failed")]
    assert (compiled["compile"], compiled["compile_line"]) == ("내 코드:6: error: ';' expected", 6)

    # 등록한 문제의 직접 입력도 첫 케이스에서 정한 모양으로 본다. 정답 풀이가 없어 reference는 없다
    assert "입력 모양과 달라요. 예: [1, 2]" in refuses("/api/run", id=pid, code="x", input="[[1, 1, 0]]")
    assert "입력 모양과 달라요" in refuses("/api/run", id=pid, code="x", input='["a", 1]')
    call("/api/language", id=pid, language="python")
    ran = call("/api/run", id=pid, code="def solution(a, b):\n    return a + b\n", input="[3, 4]")[1]
    assert (ran["status"], ran["got"]) == ("ran", "7") and "reference" not in ran and "reference_note" not in ran


def tools() -> None:
    """이 기기의 언어 도구: 일곱 언어 모두 있음·없음이 오고, 서버를 돌리는 Python은 있다. 문제 상태에도 같은 모양으로 실린다."""
    got = call("/api/tools")[1]["tools"]
    assert set(got) == set(server.check_judge().LANGUAGES) and len(got) == 7 and got["python"] is True
    assert call("/api/tools", refresh=True)[1]["tools"] == got
    state = call("/api/state", id=PID)[1]["problem"]
    assert state["tools"] == got and state["preparing"] is False  # 미리 만들기가 없으면 준비 중이 아니다


def edit_delete() -> None:
    """등록 언어, 고치기(제목만 / 글), 지우기. 기본 문제는 고치거나 지울 수 없다."""
    java = server.register({**GOOD, "language": "java"})["id"]
    assert call("/api/state", id=java)[1]["problem"]["language"] == "java"
    for bad in ("cobol", ["java"], 1):
        try:
            server.register({**GOOD, "language": bad})
            raise AssertionError("모르는 언어는 거절해야 한다")
        except server.Refuse as exc:
            assert (exc.status, exc.field) == (400, "language")

    pid = server.register(GOOD)["id"]
    with server.tutor() as t:  # 튜터가 준비해 둔 계획(모델이 만드는 것)을 손으로 넣는다
        t.adopt(pid, FIRST["ready"])
    assert call("/api/turn", id=pid, mode="chair", event="start")[0] == 200
    code = "def solution(a, b):\n    return a + b\n"
    call("/api/submit", id=pid, code=code)
    state = call("/api/state", id=pid, mode="chair")[1]
    assert state["problem"]["submitted"] == 1 and state["session"]["blocks"] and state["session"]["chair"]

    call("/api/problems/edit", id=pid, title="두 수 더하기", text=GOOD["text"], cases=GOOD["cases"])  # 제목만
    state = call("/api/state", id=pid, mode="chair")[1]
    assert state["problem"]["title"] == "두 수 더하기" and state["problem"]["submitted"] == 1 and state["session"]["blocks"] and state["session"]["chair"]
    with server.tutor() as t:
        assert t.store.load(pid).title == "두 수 더하기"

    from types import SimpleNamespace
    from unittest.mock import patch

    gone = []  # 비슷한 문항 찾기 색인에서 뺀 문항(색인은 바꿔 끼운다)
    with patch.object(server, "index", lambda: SimpleNamespace(count=lambda: 10**6, delete=gone.append)):
        call("/api/problems/edit", id=pid, title="두 수 더하기", text=GOOD["text"] + "\n\n제한사항: a, b는 정수", cases=[{"input": "[2, 3]", "expected": "5"}])  # 글과 케이스
    assert gone == [pid]
    state = call("/api/state", id=pid, mode="chair")[1]
    assert state["problem"]["text"].endswith("정수") and state["problem"]["examples"] == [{"input": "[2, 3]", "expected": "5", "note": ""}]
    assert (state["problem"]["submitted"], state["problem"]["code"]) == (1, code)  # 제출 기록과 코드는 남는다
    assert state["session"]["blocks"] == [] and state["session"]["chair"] == []  # 계획과 대화는 지워진다
    try:
        call("/api/problems/edit", id=pid, title="", text="x", cases=GOOD["cases"])
        raise AssertionError("빈 제목은 거절해야 한다")
    except server.Refuse as exc:
        assert exc.field == "title"

    with patch.object(server, "index", lambda: SimpleNamespace(count=lambda: 10**6, delete=gone.append)):
        assert call("/api/problems/delete", id=pid)[1] == {"ok": True}
    assert gone == [pid, pid]
    assert pid not in [row["id"] for row in call("/api/problems")[1]["problems"]]
    try:
        call("/api/state", id=pid)
        raise AssertionError("지운 문제는 없다")
    except server.Refuse as exc:
        assert exc.status == 404
    with server.tutor() as t:
        assert t.store.conn.execute("SELECT COUNT(*) FROM submission WHERE problem_id=?", (pid,)).fetchone()[0] == 0 and t.store.load(pid) is None
    for path, extra in (("/api/problems/delete", {}), ("/api/problems/edit", GOOD)):  # 기본 문제는 거절
        try:
            call(path, id=PID, **extra)
            raise AssertionError(path)
        except server.Refuse as exc:
            assert exc.status == 400


def own_starter() -> None:
    """등록한 문제의 시작 코드: 첫 케이스에서 형을 정해 함수 머리를 만들고, 그 머리에 맞춰 쓴 정답이 채점을 통과한다(실수는 double). 형을 못 정하면 빈 글."""
    case = {"title": "두 번째 수", "text": "배열 a의 두 번째 수를 return 하도록 solution 함수를 완성하세요.", "cases": [{"input": "[[1, 2, 3], 5]", "expected": "2"}]}
    pid = server.register({**case, "language": "java"})["id"]
    starter = call("/api/state", id=pid)[1]["problem"]["starter"]
    assert "public int solution(int[] a, int b)" in starter, starter
    if server.tools()["java"]:
        answer = starter.replace("int answer = 0;", "int answer = a[1];")
        assert answer != starter and call("/api/submit", id=pid, code=answer)[1]["ok"]
    py = call("/api/language", id=pid, language="python")[1]["problem"]["starter"]
    assert py.startswith("def solution(a, b):") and call("/api/submit", id=pid, code=py.replace("answer = 0", "answer = a[1]"))[1]["ok"]
    assert server.value_type([["a"], []]) == "string[][]" and server.value_type(5_000_000_000) == "long" and server.value_type([True]) == "bool[]"
    for given, expected in (("[[], 5]", "2"), ("[1]", "[]")):  # 빈 목록: 형을 못 정한다
        pid = server.register({**case, "cases": [{"input": given, "expected": expected}]})["id"]
        assert call("/api/state", id=pid)[1]["problem"]["starter"] == "", given
    # 실수를 받고 돌려주는 문제: double 배열과 double로 머리를 만들고, 그 머리에 맞춘 정답이 통과한다
    assert server.value_type(1.5, 2) == "double" and server.value_type([1, 2.5]) == "double[]" and server.value_type([[1.5]], [[2]]) == "double[][]"
    pid = server.register({**case, "title": "두 실수의 합", "language": "java", "cases": [{"input": "[[1.5, 2.5], 2]", "expected": "4.0"}]})["id"]
    starter = call("/api/state", id=pid)[1]["problem"]["starter"]
    assert "public double solution(double[] a, int b)" in starter and "double answer = 0.0;" in starter, starter
    if server.tools()["java"]:
        assert call("/api/submit", id=pid, code=starter.replace("double answer = 0.0;", "double answer = a[0] + a[1];"))[1]["ok"]
    py = call("/api/language", id=pid, language="python")[1]["problem"]["starter"]
    assert py.startswith("def solution(a, b):") and call("/api/submit", id=pid, code=py.replace("answer = 0.0", "answer = a[0] + a[1]"))[1]["ok"], py


def case_shapes() -> None:
    """케이스끼리 모양 검사(등록·수정): 인자 수, 자리마다의 형, 기대 결과의 형. 시작 코드는 모든 케이스를 보고 정한다. 검사 전에 등록한 문항도 열고 푼다."""
    def why(cases, path="/api/problems/new", **extra) -> tuple[str, str]:
        try:
            call(path, **{**GOOD, **extra, "cases": cases})
        except server.Refuse as exc:
            return str(exc), exc.field
        raise AssertionError(cases)

    one = {"input": "[[1, 2, 3]]", "expected": "6"}
    assert why([one, {"input": "", "expected": ""}, {"input": "[1, 2, 3, 4]", "expected": "10"}]) == (
        "3번 케이스는 넣을 값이 4개인데 1번 케이스는 1개예요. 배열 하나를 넘기려면 [[1, 2, 3]]처럼 한 번 더 감싸요.", "case-input-3")  # 빈 줄도 번호를 센다(화면의 줄 번호)
    assert why([{"input": "[1]", "expected": "1"}, {"input": '["a"]', "expected": "1"}]) == ("2번 케이스의 1번째 값은 문자열인데 1번 케이스는 정수예요.", "case-input-2")
    assert why([{"input": "[1]", "expected": "1"}, {"input": "[2]", "expected": '"x"'}]) == ("2번 케이스의 기대 결과는 문자열인데 1번 케이스는 정수예요.", "case-expected-2")
    assert why([one, {"input": "[[[1]]]", "expected": "1"}])[0] == "2번 케이스의 1번째 값은 정수 2차원 배열인데 1번 케이스는 정수 배열이에요."
    assert why([{"input": "[[]]", "expected": "0"}, {"input": "[[1]]", "expected": "1"}, {"input": '[["a"]]', "expected": "1"}])[0] == "3번 케이스의 1번째 값은 문자열 배열인데 2번 케이스는 정수 배열이에요."  # 빈 목록은 어울린다
    assert why([{"input": "[true]", "expected": "1"}, {"input": "[1]", "expected": "1"}])[0] == "2번 케이스의 1번째 값은 정수인데 1번 케이스는 참·거짓이에요."
    for cases, field in (([{"input": '[[1, "a"]]', "expected": "1"}], "case-input-1"), ([{"input": "[1]", "expected": "1"}, {"input": "[2]", "expected": '[[1], ["a"]]'}], "case-expected-2")):
        assert why(cases) == (f"{field[-1]}번 케이스의 목록에 서로 다른 종류의 값이 섞여 있어요.", field)  # 한 목록 안에 종류가 다른 값은 등록 때 거절한다
    nulls = server.register({**GOOD, "cases": [{"input": "[[1, null, 2.5]]", "expected": "null"}, {"input": "[[]]", "expected": "null"}]})["id"]  # null은 섞여도 되고, 정수와 실수는 어울린다
    assert call("/api/state", id=nulls)[1]["problem"]["starter"] == ""  # 기대 결과가 모두 null이면 형을 정하지 못한다(화면이 그 까닭을 알린다)
    mixed = server.register({**GOOD, "language": "java", "cases": [{"input": "[[], 5]", "expected": "0"}, {"input": "[[1, 2], 3]", "expected": "2"}, {"input": "[[1], 1.5]", "expected": "1"}]})["id"]
    assert "public int solution(int[] a, double b)" in call("/api/state", id=mixed)[1]["problem"]["starter"]  # 정수와 실수가 섞인 자리는 double
    pid = server.register({**GOOD, "language": "java", "cases": [{"input": "[[], 5]", "expected": "0"}, {"input": "[[1, 2], 5000000000]", "expected": "2"}]})["id"]
    assert "public int solution(int[] a, long b)" in call("/api/state", id=pid)[1]["problem"]["starter"]  # 빈 목록은 다른 케이스에서, 32비트를 넘는 수는 long
    assert "입력 모양과 달라요" in refuses("/api/run", id=pid, code="x", input='[["a"], 1]') and "입력 모양과 달라요" in refuses("/api/run", id=pid, code="x", input="[[1], 1, 2]")
    assert why([{"input": "[1, 2]", "expected": "3"}, {"input": "[1]", "expected": "3"}], "/api/problems/edit", id=pid)[1] == "case-input-2"  # 수정에서도 같은 검사
    # 검사 전에 등록된 어긋난 문항: 열리고(시작 코드 없음) 제출도 된다
    rows = server.read_json(server.PROBLEMS_FILE, [])
    rows.append({"id": "u0000beef", "title": "예전 문항", "language": "python", "text": "옛 글", "cases": [{"id": "1", "input": "[1, 2]", "expected": "3"}, {"id": "2", "input": "[[1, 2]]", "expected": "3"}]})
    server.write_json(server.PROBLEMS_FILE, rows)
    server.reload_problems()
    old = call("/api/state", id="u0000beef")[1]["problem"]
    assert old["starter"] == "" and len(old["examples"]) == 2
    assert call("/api/submit", id="u0000beef", code="def solution(*a):\n    return 3\n")[1]["ok"]
    assert call("/api/run", id="u0000beef", code="def solution(*a):\n    return 3\n", input="[1]")[1]["status"] == "ran"  # 형을 정하지 못하면 모양을 보지 않는다


def table() -> None:
    """입출력 예 표에서 케이스 채우기(규칙만, 모델 0회): 마크다운 표, 탭 표, 파이썬식 값, 읽지 못하는 줄, 표 없음, 결과 머리가 아닌 표. 표 머리의 이름은 시작 코드의 인자 이름."""
    want = {"names": ["numbers", "k"], "cases": [{"input": "[[1, 2, 3], 2]", "expected": "5"}, {"input": "[[4, 5], 1]", "expected": "4"}], "skipped": 0}
    md = "## 문제 설명\n배열 numbers와 k가 주어집니다.\n\n| x | y |\n|---|---|\n| 1 | 2 |\n\n## 입출력 예\n| numbers | k | result |\n|---|:---:|---|\n| [1, 2, 3] | 2 | 5 |\n| [4,5] | 1 | 4 |\n\n입출력 예 설명"
    assert found(text=md) == want  # 결과 머리가 아닌 앞 표는 고르지 않는다
    assert found(text="입출력 예\nnumbers\tk\tresult\n[1, 2, 3]\t2\t5\n[4, 5]\t1\t4\n입출력 예 설명\n...") == want  # 화면에서 복사한 표
    assert found(text="numbers   k   return\n[1, 2, 3]   2   5\n[4, 5]  1  4") == want  # 둘 이상의 공백
    assert found(text="입출력 예\nnumbers k result\n[1, 2, 3] 2 5\n[4,5] 1 4\n입출력 예 설명\n입출력 예 #1") == want  # PDF에서 읽은 글: 칸이 공백 하나로 접힌 표
    assert found(text="s flag answer\n'a b' True None\n['a', 'b'] False [1, 2]\n1,000 1 2") == {
        "names": ["s", "flag"], "cases": [{"input": '["a b", true]', "expected": "null"}, {"input": '[["a", "b"], false]', "expected": "[1, 2]"}], "skipped": 0,
        "missed": ["1,000 1 2"]}  # 파이썬식 값, 읽지 못하는 줄에서 끝난다. 예시처럼 생긴 그 줄은 알린다
    assert found(text="두 수를 더한 결과\n3 5")["cases"] == []  # 값의 수가 머리 낱말 수와 다르면 표가 아니다
    py = "| s | flag | answer |\n|--|--|--|\n| 'ab' | True | None |\n| ['a', 'b',] | False | [1, 2,] |\n| abc | 1 | 2 |\n| 1,000 | 1 | 2 |\n| 1 | 2 |\n| [1] | 1e999 | 1 |"
    assert found(text=py) == {"names": ["s", "flag"], "cases": [{"input": '["ab", true]', "expected": "null"}, {"input": '[["a", "b"], false]', "expected": "[1, 2]"}], "skipped": 4}
    for text in ("표가 없는 글", "| a | b | count |\n|---|---|---|\n| 1 | 2 | 3 |", "a\tresult", ""):
        assert found(text=text) == {"names": [], "cases": [], "skipped": 0}, text
    assert "글이어야" in refuses("/api/problems/cases", text=["x"])
    ocr = "temps result\n[1, 2, 3] 2\n[3, 2, 1, 5] 1\n0, 2, 2, 3, 4,5, 1]   4\n\n입출력 예 설명"  # 글자 읽기가 깨뜨린 예시 한 줄
    assert {"where": "입출력 예", "note": "예시 한 줄을 읽지 못했어요: `0, 2, 2, 3, 4,5, 1] 4`"} in server.read_doubts(ocr, "function")
    assert "missed" not in found(text=ocr.replace("0, 2, 2, 3, 4,5, 1]   4", "입출력 예 #1"))
    boj = "문제\n두 수의 합을 출력한다.\n\n예제 입력 1\n1 2\n\n예제 출력 1\n3\n"  # 함수 방식에 예제 구역이 있는 글: 다른 방식(표준 입출력)에서 찾은 수를 준다
    assert call("/api/problems/cases", text=boj)[1] == {"names": [], "cases": [], "skipped": 0, "other": 1}
    assert call("/api/problems/cases", text=md, mode="program")[1]["other"] == 2 and call("/api/problems/cases", text=md)[1]["other"] == 0

    body = {**GOOD, "language": "java", "cases": want["cases"]}
    pid = server.register({**body, "names": ["numbers", "k"]})["id"]
    assert "public int solution(int[] numbers, int k)" in call("/api/state", id=pid)[1]["problem"]["starter"]
    assert call("/api/language", id=pid, language="python")[1]["problem"]["starter"].startswith("def solution(numbers, k):")
    for names, head in ((["in", "class"], "def solution(in_, class_):"), (["1a", "k"], "def solution(a, b):"), (["k", "k"], "def solution(a, b):"), (["k"], "def solution(a, b):"), ("k", "def solution(a, b):")):
        other = server.register({**body, "language": "python", "names": names})["id"]
        assert call("/api/state", id=other)[1]["problem"]["starter"].startswith(head), names
    call("/api/problems/edit", id=pid, **body)  # names가 없으면 예전 이름 그대로
    assert call("/api/state", id=pid)[1]["problem"]["starter"].startswith("def solution(numbers, k):")
    call("/api/problems/edit", id=pid, **body, names=["arr", "answer"])
    assert call("/api/state", id=pid)[1]["problem"]["starter"].startswith("def solution(arr, answer_):")


def hidden_cases() -> None:
    """숨김 케이스: 공개 예시만 문제 화면·예시 실행에, 제출은 모두 돌리고 숨긴 것은 통과 여부만. 수정 화면(own_cases)은 값을 본다. 공개 예시가 없으면 거절."""
    secret = '[777, 1]'
    cases = [{"input": "[1, 2]", "expected": "3"}, {"input": secret, "expected": "778", "hidden": True}, {"input": "[5, 5]", "expected": "10", "hidden": "true"}]  # 문자열 "true"는 숨김이 아니다
    pid = server.register({**GOOD, "cases": cases})["id"]
    assert [case.get("kind") for case in server.PROBLEMS[pid].cases] == [None, "accuracy", None]
    state = call("/api/state", id=pid)[1]["problem"]
    assert [x["input"] for x in state["examples"]] == ["[1, 2]", "[5, 5]"] and state["cases"] == {"example": 2, "accuracy": 1, "efficiency": 0}
    assert [x["hidden"] for x in state["own_cases"]] == [False, True, False] and state["own_cases"][1]["input"] == secret  # 수정 화면은 숨긴 값도 본다
    assert "own_cases" not in call("/api/state", id=PID)[1]["problem"]
    ran = call("/api/run", id=pid, code="def solution(a, b):\n    return a + b if a < 100 else 0\n")[1]
    assert ran["ok"] and [case["kind"] for case in ran["cases"]] == ["example", "example"]  # 예시 실행은 공개 예시만
    wrong = call("/api/submit", id=pid, code="def solution(a, b):\n    return a + b if a < 100 else 0\n")[1]
    assert not wrong["ok"] and wrong["score"]["accuracy"] == [2, 3] and secret not in json.dumps(wrong) and "778" not in json.dumps(wrong)
    hid = next(case for case in wrong["cases"] if case["kind"] == "accuracy")
    assert hid["status"] == "failed" and not {"input", "expected", "got"} & hid.keys()  # 숨긴 케이스는 통과 여부만
    assert "입력 모양과 달라요. 예: [1, 2]" in refuses("/api/run", id=pid, code="x", input='["a", "b"]')
    try:
        server.register({**GOOD, "cases": [{"input": "[1, 2]", "expected": "3", "hidden": True}, {"input": "", "expected": ""}]})
        raise AssertionError("공개 예시가 없으면 거절해야 한다")
    except server.Refuse as exc:
        assert (str(exc), exc.field) == ("공개 예시가 하나는 있어야 해요.", "case-hidden-1")
    call("/api/problems/edit", id=pid, title="숨김 바꿈", text=GOOD["text"], cases=[cases[0], {**cases[1], "hidden": False}])
    assert len(call("/api/state", id=pid)[1]["problem"]["examples"]) == 2


def explicit_mode() -> None:
    """방식을 문항에 적고 채점기에 명시한다: 글에 '첫째 줄'(채점기가 프로그램 방식으로 짐작하는 말)이 있어도 함수 방식 문항은 함수 방식으로 채점한다."""
    pid = server.register({**GOOD, "text": "첫째 줄에 정수가 주어집니다. 두 수의 합을 돌려주세요."})["id"]
    assert server.PROBLEMS[pid].mode == "function" and server.check_judge().decide_mode(server.PROBLEMS[pid].text, "", server.check_judge().load_language("python"))[0] == "program"
    assert call("/api/submit", id=pid, code="def solution(a, b):\n    return a + b\n")[1]["ok"]
    assert call("/api/run", id=pid, code="def solution(a, b):\n    return a + b\n", input="[2, 3]")[1]["got"] == "5"
    assert server.PROBLEMS[PID].mode == "function"  # 기본 문제도 함수 방식


PROGRAM = {"title": "A+B", "text": "첫째 줄에 A와 B가 주어진다. A+B를 출력한다.", "mode": "program",
           "cases": [{"input": "3 5\n", "expected": "8\n"}, {"input": "", "expected": ""}, {"input": "10 20", "expected": "30", "hidden": True}]}
PY_SUM = "a, b = map(int, input().split())\nprint(a + b)\n"


def program_mode() -> None:
    """표준 입출력(프로그램 방식) 문항: 등록 검사, 시작 코드, 채점(Python·Java), 틀린 출력은 예시의 입력·기대·내 출력, 숨긴 케이스는 상태만,
    채점기는 다른 방식으로 다시 돌리지 않는다, 직접 입력 실행, 예제 구역에서 채우기, 수정에서 방식은 그대로."""
    pid = server.register(PROGRAM)["id"]
    assert server.PROBLEMS[pid].mode == "program" and server.read_json(server.PROBLEMS_FILE, [])[-1]["mode"] == "program"
    assert [(c["input"], c["expected"], c.get("kind")) for c in server.PROBLEMS[pid].cases] == [("3 5\n", "8\n", None), ("10 20\n", "30", "accuracy")]  # 입력은 줄바꿈으로 끝나게
    for cases, words in (([{"input": "1", "expected": " "}], "1번 케이스의 기대 출력을 적어 주세요."), ([{"input": "1" * 20_001, "expected": "1"}], "입력은 20,000자까지"),
                         ([{"input": "1", "expected": "1" * 20_001}], "기대 출력은 20,000자까지"), ([{"input": "1", "expected": "1", "hidden": True}], "공개 예시가 하나는")):
        assert words in refuses("/api/problems/new", **{**PROGRAM, "cases": cases}), words
    assert "고를 수 없는 푸는 방식" in refuses("/api/problems/new", **{**PROGRAM, "mode": "stdin"})
    hello = server.register({**PROGRAM, "cases": [{"input": " ", "expected": "Hello"}], "names": ["a"]})["id"]  # 입력 없는 문제, 인자 이름은 버린다
    assert server.PROBLEMS[hello].cases == [{"id": "1", "input": "", "expected": "Hello"}] and not hasattr(server.PROBLEMS[hello], "names")
    assert call("/api/submit", id=hello, code="print('Hello')\n")[1]["ok"]

    state = call("/api/state", id=pid)[1]["problem"]
    assert (state["mode"], state["starter"], state["examples"]) == ("program", server.program_stub("python"), [{"input": "3 5\n", "expected": "8\n", "note": ""}])
    assert call("/api/submit", id=pid, code=PY_SUM)[1]["ok"]
    wrong = call("/api/submit", id=pid, code=PY_SUM.replace("a + b", "a - b"))[1]
    example, hidden = wrong["cases"]
    assert not wrong["ok"] and (example["input"], example["expected"], example["got"], example["status"]) == ("3 5\n", "8\n", "-2\n", "failed")
    assert hidden["status"] == "failed" and not {"input", "expected", "got"} & hidden.keys() and "10 20" not in json.dumps(wrong)  # 숨긴 케이스는 상태만
    crashed = call("/api/submit", id=pid, code="print(1 / 0)\n")[1]
    assert crashed["status"] == "runtime_error" and crashed["cases"][0]["error"].startswith("ZeroDivisionError") and crashed["cases"][0]["line"] == 1
    entry = call("/api/submit", id=pid, code="def solution(a, b):\n    return a + b\n")[1]  # 함수만 있다: 함수 방식으로 다시 돌리지 않는다
    assert entry["status"] == "entry_missing" and not entry["cases"]
    assert server.clean('File "/private/var/folders/x/algoblock-check-ab12/main.py", line 1\n\tat Main.main(Main.java:5)') == 'File "내 코드", line 1\n\tat Main.main(내 코드:5)'

    # 직접 입력: 글 그대로 넣고, 출력 전체를 돌려준다. 예시 실행은 공개 예시만
    ran = call("/api/run", id=pid, code="import sys\nprint(sys.stdin.read().split())\n", input="1 2\r\n3")[1]
    assert (ran["status"], ran["input"], ran["got"], ran["stdout"], ran["error"]) == ("ran", "1 2\n3\n", "['1', '2', '3']\n", "", "") and "reference" not in ran
    broke = call("/api/run", id=pid, code="print('before')\nprint(1 / 0)\n", input="")[1]
    assert (broke["status"], broke["got"]) == ("runtime_error", "before\n") and broke["error"].startswith("ZeroDivisionError")
    assert "20,000자" in refuses("/api/run", id=pid, code=PY_SUM, input="1" * 20_001)
    assert [c["kind"] for c in call("/api/run", id=pid, code=PY_SUM)[1]["cases"]] == ["example"]

    if server.tools()["java"]:
        starter = call("/api/language", id=pid, language="java")[1]["problem"]["starter"]
        assert "public class Main" in starter and "public static void main(String[] args)" in starter
        java = starter.replace("        // 여기에 풀이를 써요\n", "        StringTokenizer st = new StringTokenizer(br.readLine());\n"
                               "        System.out.println(Integer.parseInt(st.nextToken()) + Integer.parseInt(st.nextToken()));\n")
        assert java != starter and call("/api/submit", id=pid, code=java)[1]["ok"]
        assert call("/api/submit", id=pid, code="class Solution {\n    public int solution(int a, int b) { return a + b; }\n}\n")[1]["status"] == "entry_missing"
        call("/api/language", id=pid, language="python")

    # 수정: 방식은 보내도 바뀌지 않고, 케이스는 프로그램 방식 규칙으로 본다
    call("/api/problems/edit", id=pid, title="A+B 고침", text=PROGRAM["text"], mode="function", cases=[{"input": "3 5", "expected": "8"}])
    assert server.PROBLEMS[pid].mode == "program" and server.PROBLEMS[pid].cases == [{"id": "1", "input": "3 5\n", "expected": "8"}]

    # 답 비교 표시는 사용자가 켤 때만(글의 낱말로 짐작하지 않는다): 실수 답은 0.000001 차이까지 같게, 답이 여럿이면 다른 답을 틀렸다고 단정하지 않고 숨은 테스트를 만들지 않는다
    third = {**PROGRAM, "text": PROGRAM["text"] + " 실수로 출력하며 오차는 허용한다.", "cases": [{"input": "1 3", "expected": "0.333333"}]}
    divide = "a, b = map(int, input().split())\nprint(a / b)\n"
    plain = server.register(third)["id"]
    assert not call("/api/submit", id=plain, code=divide)[1]["ok"] and not hasattr(server.PROBLEMS[plain], "float_output")  # 표시가 없으면 글자 그대로
    floated = server.register({**third, "float_output": True})["id"]
    assert call("/api/submit", id=floated, code=divide)[1]["ok"]
    many = server.register({**PROGRAM, "many_answers": True})["id"]
    other = call("/api/submit", id=many, code=PY_SUM.replace("a + b", "a - b"))[1]
    assert not other["ok"] and [c.get("error") for c in other["cases"]] == [MANY_ANSWERS] * 2, other
    assert (server.cross_mode(many), server.cross_mode(plain), server.problem_shape(many, "python")["many_answers"]) == (None, "program", True)
    assert call("/api/state", id=many)[1]["problem"]["many_answers"] is True
    call("/api/problems/edit", id=many, title="A+B", text=PROGRAM["text"], cases=PROGRAM["cases"], many_answers=False, float_output=True)  # 수정에서 바꾼다
    assert (getattr(server.PROBLEMS[many], "many_answers", False), server.PROBLEMS[many].float_output, server.cross_mode(many)) == (False, True, "program")
    fn = server.register({**GOOD, "float_output": True, "many_answers": True})["id"]  # 함수 방식에는 두지 않는다
    assert not {"float_output", "many_answers"} & vars(server.PROBLEMS[fn]).keys()

    # 예제 구역에서 채우기(규칙, 모델 0회): 번호끼리 짝, '복사' 꼬리, 코드 울타리, 빈 줄 둘에서 끝
    text = ("문제\nA+B를 구하세요.\n\n입력\n첫째 줄에 A와 B가 주어진다.\n\n출력\n첫째 줄에 A+B를 출력한다.\n\n예제 입력 1 복사\n1 2\n예제 출력 1 복사\n3\n\n"
            "예제 입력 2\n```\n10 20\n```\n예제 출력 2\n30\n  \n\n힌트\n없음")
    want = [{"input": "1 2\n", "expected": "3\n"}, {"input": "10 20\n", "expected": "30\n"}]
    assert found(text=text, mode="program") == {"names": [], "cases": want, "skipped": 0}
    assert found(text="Sample Input 1\n1 2\nSample Output 1\n3\n\nsample input 2\n10 20\nSAMPLE OUTPUT 2\n30", mode="program")["cases"] == want
    assert found(text="## 입력 예 1\n1 2\n\n## 출력 예 1\n3\n\n## 출력 예 2\n\n## 입력 예 3\n1", mode="program") == {"names": [], "cases": want[:1], "skipped": 2}
    assert found(text="예제 입력 1\n예제 출력 1\nHello World!", mode="program")["cases"] == [{"input": "", "expected": "Hello World!\n"}]
    # 예제 출력 뒤에 빈 줄 하나로 붙은 글(힌트·출처)은 끊는 규칙을 바꾸지 않고 알린다: 등록 화면의 케이스 알림과 파일 읽기의 '확인이 필요한 곳'
    tail = "예제 입력 1 복사\n3\n1 2 3\n예제 출력 1 복사\n6\n\n힌트\n1+2+3=6이다.\n\n출처\nfoo"
    spilled = found(text=tail, mode="program")
    assert spilled["cases"] == [{"input": "3\n1 2 3\n", "expected": "6\n\n힌트\n1+2+3=6이다.\n\n출처\nfoo\n"}] and spilled["spill"] == [server.SPILL.format(n=1)], spilled
    assert {"where": "입출력 예", "note": server.SPILL.format(n=1)} in server.read_doubts(tail, "program")
    assert "spill" not in found(text="예제 입력 1\n2\n예제 출력 1\n1 2\n3 4", mode="program")  # 빈 줄 없는 여러 줄 출력은 알리지 않는다
    assert found(text=text)["cases"] == [] and found(text="표가 없는 글", mode="program")["cases"] == []


def program_tutor() -> None:
    """튜터가 표준 입출력 문항에서도 돈다(가짜 모델): 풀이 가이드를 만들 때 표준 입출력 프로그램으로 쓰라고 하고, 그 정답 코드는 문항의 방식(program)으로 채점되며,
    블록의 틀 줄은 진입점(import, input = sys.stdin.readline, class Main, main 머리, 닫는 괄호)이다. 저장 질문으로 시작하고 블록 코드 확인은 모델 0회."""
    hints = ["무엇을 읽어야 할까요?", "'첫째 줄에 A와 B'는 몇 개를 읽으라는 걸까요?", "입력이 3 5라면 무엇을 읽나요?"]
    guides = {"python": "import sys\ninput = sys.stdin.readline\na, b = map(int, input().split())\nprint(a + b)",
              "java": "import java.io.*;\nimport java.util.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n"
                      "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        StringTokenizer st = new StringTokenizer(br.readLine());\n"
                      "        int a = Integer.parseInt(st.nextToken());\n        int b = Integer.parseInt(st.nextToken());\n        System.out.println(a + b);\n    }\n}"}
    heads = {"python": ["import sys", "input = sys.stdin.readline"], "java": guides["java"].splitlines()[:5]}  # 모을 때 붙는 틀 줄
    for language in [lang for lang in guides if server.tools()[lang]]:
        code, cut = guides[language], 3 if language == "python" else 9
        lines = code.splitlines()
        blocks = [{"id": "b1", "kind": "var_from_problem", "name": "두 수 읽기", "goal": "A와 B를 읽는다", "reference": "", "lines": [1, cut], "checks": ["A와 B를 읽는다"], "hints": hints},
                  {"id": "b2", "kind": "var_during", "name": "합 출력", "goal": "A+B를 출력한다", "reference": "", "lines": [cut + 1, len(lines)], "checks": ["합을 출력한다"], "hints": hints}]
        solved = {"clues": ["'A+B를 출력한다' → 두 수를 더해 출력한다"], "approach": "두 수를 읽어 더한 값을 출력한다.", "steps": ["두 수를 읽는다 — 입력", "합을 출력한다 — 답"], "code": code}
        fake = FakeLlm({"plan.solve": [solved], "plan.draft_blocks": [{"algorithm": "hash", "out_of_scope": False, "blocks": blocks}]})
        pid = server.register({**PROGRAM, "language": language})["id"]
        with use_llm(fake):
            with server.tutor() as t:
                t.store.put_fact(pid, "두 정수의 합", [])
                assert t.prepare(pid).status == 200, language
                guide = t.store.load(pid).solution
            assert (guide.code, guide.verified) == (code, True), (language, guide)  # 정답 코드를 표준 입출력 방식으로 채점해 통과했다
            asked = "\n".join(m["content"] for c in fake.calls if c["task"] == "plan.solve" for m in c["messages"])
            assert "표준 입력을 읽어 표준 출력에 쓰는 프로그램으로 쓴다" in asked and "solution 함수 하나로" not in asked  # 등록한 방식을 준다(문제 글로 고르게 하지 않는다)
            first = call("/api/turn", id=pid, mode="chair", event="start")[1]["messages"][-1]["text"]
            assert first == hints[0], first  # 저장 질문(모델 0회)
            got = call("/api/state", id=pid, mode="chair")[1]["session"]["blocks"][0]
            assert not {"indent", "head", "tail"} & set(got), (language, got)  # 틀 정보는 화면에 싣지 않는다(모으기는 서버가 한다)
            assert call("/api/fill", id=pid, block_id="b1")[1]["open_count"] == 2  # 1번 블록을 채워 찾았다
            ref = "\n".join(lines[len(heads[language]):cut])  # 틀 줄 없이 알맹이만 적는다(실행해 확인한다)
            parts = call("/api/compose", id=pid, mode="chair", blocks={"b1": {"code": ref, "by": "me"}})[1]["parts"]
            assert parts[0][1].startswith("\n".join(heads[language]) + "\n"), (language, parts)  # 서버가 틀 줄을 붙여 모은다
            said = call("/api/turn", id=pid, mode="chair", event="block_filled", block_id="b1", code=ref)[1]["messages"][-1]["text"]
            # 방식은 서버가 넘긴다: def main이 없는 Python 표준 입출력 코드도 프로그램으로 잇는다. 숨긴 케이스가 있어 '예시로만' 말은 없다
            assert said == "통과예요. 이 블록의 코드는 할 일을 해내요.", (language, said)
            # 가짜 모델에 단순 풀이가 없다: 대조를 하지 못하고(예시만 통과) 블록을 짠다
            assert [c["task"] for c in fake.calls] == ["plan.solve", "plan.brute", "plan.draft_blocks"], [c["task"] for c in fake.calls]


def own_guide() -> None:
    """등록한 문제도 엔진이 만들어 둔 풀이 가이드가 있으면 통과 뒤 해설과 실전 신호(가이드의 단서)를 본다. 잠금은 기본 문제와 같다."""
    pid = server.register(GOOD)["id"]
    assert call("/api/state", id=pid)[1]["problem"]["study"]["has_guide"] is False
    ready = {**FIRST["ready"], "solution": {**FIRST["ready"]["solution"], "verified": False, "clues": ["'제목이 같으면 같은 책입니다' → 개수를 센다", "입력이 크다"]}}
    with server.tutor() as t:  # 튜터가 준비해 둔 가이드(모델이 만드는 것)를 손으로 넣는다
        t.adopt(pid, ready)
    assert call("/api/state", id=pid)[1]["problem"]["study"]["has_guide"] is True
    assert call("/api/solution", id=pid)[0] == 409
    assert call("/api/submit", id=pid, code="def solution(a, b):\n    return a + b\n")[1]["ok"]
    status, sol = call("/api/solution", id=pid)
    assert status == 200 and sol["signals"] == [{"phrase": "제목이 같으면 같은 책입니다", "means": "개수를 센다"}, {"phrase": "", "means": "입력이 크다"}]
    assert (sol["code"], sol["language"], sol["verified"], sol["next"]) == (CODE, "python", False, None)
    with server.tutor() as t:
        assert not t.store.study(pid)["solution_before_pass"]  # 통과한 뒤에 열었다
    assert [row["phrase"] for row in server.clue_signals(["'1. 금메달이 앞섭니다.' 와 '2. 은메달' → 순서", "“\"문자열\" s” → 뜻", " '한 번만' → 센다"])] == [
        "'1. 금메달이 앞섭니다.' 와 '2. 은메달'", '"문자열" s', "한 번만"]  # 바깥 한 쌍만 벗기고, 여러 인용을 이은 구절은 그대로


def prep_failed() -> None:
    """뒤에서 미리 만들기가 실패하면(엔진은 예외 대신 실패 결과를 돌려준다) 상태에 prepare_failed가 실리고, 다시 열면(다시 준비) 같은 길로 다시 만든다."""
    import contextlib
    import io
    import time
    from tutor.main import Outcome

    pid = server.register(GOOD)["id"]
    tries = []
    def failing(self, problem_id):
        tries.append(problem_id)
        return Outcome(502, {"detail": {"code": "invalid_output", "message": "블록이 풀이 코드를 빠짐없이 나누지 않았습니다"}})
    with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", failing), contextlib.redirect_stderr(io.StringIO()):
        for n in (1, 2):
            call("/api/state", id=pid, open=True)  # 문제를 열면(다시 준비도 같은 요청) 뒤에서 준비한다
            for _ in range(200):
                if pid not in server.PREPARING:
                    break
                time.sleep(0.02)
            body = call("/api/state", id=pid)[1]["problem"]
            assert body["prepare_failed"] and not body["preparing"] and pid not in server.PREPARED and tries == [pid] * n, (body, tries)
    server.PREP_FAILED.discard(pid)
    assert not call("/api/state", id=pid)[1]["problem"]["prepare_failed"]


def stale_save() -> None:
    """언어를 바꾸는 사이에 온 옛 언어의 코드·블록은 저장하지 않는다(어느 언어의 코드인지 같이 온다)."""
    pid = server.register(GOOD)["id"]  # 언어는 python
    before = call("/api/state", id=pid)[1]["problem"]["code"]
    assert call("/api/code", id=pid, code="class Solution {}", language="java")[1] == {"stale": True}
    assert call("/api/blocks", id=pid, blocks={"b1": {"code": "int x;", "by": "me"}}, language="java")[1] == {"stale": True}
    body = call("/api/state", id=pid)[1]
    assert body["problem"]["code"] == before and body["blocks"] == {}, body["problem"]["code"]
    assert call("/api/code", id=pid, code="def solution(a, b):\n    return a + b\n", language="python")[1] == {"ok": True}
    assert call("/api/state", id=pid)[1]["problem"]["code"].startswith("def solution")


def builtin_prepare() -> None:
    """기본 문제는 열기만 해서는(다른 언어여도) 미리 만들기를 부르지 않는다. 등록한 문제는 부른다."""
    tries, pid = [], server.register(GOOD)["id"]
    with server.tutor() as t:
        row = next(row for row in ROWS if row["id"] != PID and t.store.load(row["id"]) is None)
    with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server, "prepare_later", tries.append), \
            patch.dict(server.BUILTIN[row["id"]], {"languages": [*row["languages"], "java"]}):  # 시험용 묶음은 python만 싣는다
        assert not call("/api/language", id=row["id"], language="java")[1]["problem"]["preparing"]
        body = call("/api/state", id=row["id"], open=True)[1]["problem"]
        assert body["language"] == "java" and not body["preparing"] and tries == [], tries
        call("/api/state", id=pid, open=True)
        assert tries == [pid], tries
    call("/api/language", id=PID, language="python")  # 마지막 언어를 되돌린다


def checkpoints() -> None:
    """체크포인트: 언어마다 한 벌. 되돌리면 코드와 블록 칸만 그것으로 바뀐다. 없으면 404. 문항을 지우거나 글을 고치면 함께 지운다."""
    pid = server.register(GOOD)["id"]
    try:
        call("/api/checkpoint/restore", id=pid)
        raise AssertionError("체크포인트가 없으면 404")
    except server.Refuse as exc:
        assert (exc.status, str(exc)) == (404, "남겨 둔 체크포인트가 없어요.")
    assert call("/api/state", id=pid)[1]["problem"]["checkpoint_at"] is None
    blocks = {"b1": {"code": "x = 1", "by": "me"}}
    at = call("/api/checkpoint", id=pid, code="def solution(a, b):\n    return a + b\n", blocks=blocks)[1]["at"]
    call("/api/code", id=pid, code="고친 코드")
    call("/api/blocks", id=pid, blocks={})
    call("/api/submit", id=pid, code="def solution(a, b):\n    return 0\n")
    back = call("/api/checkpoint/restore", id=pid)[1]
    assert (back["problem"]["code"], back["blocks"], back["problem"]["checkpoint_at"], back["problem"]["submitted"]) == ("def solution(a, b):\n    return a + b\n", blocks, at, 1)
    assert refuses("/api/checkpoint", id=pid, code=1) and refuses("/api/checkpoint", id=pid, code="", blocks={"b1": "x"})

    java = call("/api/language", id=pid, language="java")[1]["problem"]  # 언어마다 따로
    assert java["checkpoint_at"] is None
    try:
        call("/api/checkpoint/restore", id=pid)
        raise AssertionError("java에는 체크포인트가 없다")
    except server.Refuse as exc:
        assert exc.status == 404
    call("/api/checkpoint", id=pid, code="class Solution {}", blocks={})
    assert call("/api/language", id=pid, language="python")[1]["problem"]["checkpoint_at"] == at
    assert call("/api/checkpoint/restore", id=pid)[1]["problem"]["code"].startswith("def solution(a, b)")

    call("/api/problems/edit", id=pid, title="제목만", text=GOOD["text"], cases=GOOD["cases"])  # 제목만 고치면 남는다
    assert call("/api/state", id=pid)[1]["problem"]["checkpoint_at"] == at
    call("/api/problems/edit", id=pid, title="제목만", text=GOOD["text"] + "!", cases=GOOD["cases"])
    assert call("/api/state", id=pid)[1]["problem"]["checkpoint_at"] is None
    call("/api/checkpoint", id=pid, code="x", blocks={})
    call("/api/problems/delete", id=pid)
    assert pid not in server.read_json(server.CHECKPOINTS_FILE, {})


def compose() -> None:
    """모으기는 서버 한 곳에서 블록 코드 확인과 같은 framed로 한다. 빈 블록은 빠지고, 블록 2에 머리 줄을 적어도 확인이 돌린 프로그램과 같은 글이다."""
    from tutor.common.solution import spliced

    def text(parts):  # 블록 주석과 빈 줄을 뺀 글
        return "\n".join(row for _, part in parts for row in part.split("\n") if row.strip() and not row.strip().startswith("# 블록"))

    b1 = "\n".join(row[4:] for row in LINES[1:5])
    parts = call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": b1, "by": "me"}, "b2": {"code": "\n".join(LINES[5:]), "by": "tutor"}})[1]["parts"]
    assert [i for i, _ in parts] == [0, 1] and parts[0][1].startswith("def solution(loans, k):\n    # 블록 1 · ") and text(parts) == CODE, parts
    assert [i for i, _ in call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": "  ", "by": "me"}, "b2": {"code": "return []", "by": "me"}})[1]["parts"]] == [1]
    head2 = "def solution(loans, k):\n" + "\n".join(LINES[5:])  # 블록 2에 머리 줄을 적었다
    parts = call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": b1, "by": "me"}, "b2": {"code": head2, "by": "me"}})[1]["parts"]
    ran = spliced(["\n".join(LINES[:5]), "\n".join(LINES[5:])], 1, head2, "python", {0: b1})
    assert text(parts) == "\n".join(row for row in ran.split("\n") if row.strip()), (parts, ran)  # 확인이 돌린 프로그램과 같은 글
    assert text(parts) == CODE, parts  # 블록 2의 머리 줄은 떼고(앞 블록 자리의 틀이 넣었다) 몸통은 제자리에
    assert call("/api/compose", id=PID, mode="guide", blocks={})[1]["parts"] == []
    with server.tutor() as t:  # 튜터의 풀이를 확인하지 못했으면 계획 코드의 틀이 아니라 시작 코드의 틀 안에 놓는다
        ctx = t.store.load(PID)
        verified = ctx.solution.verified
        t.store.conn.execute("UPDATE solution SET verified = 0 WHERE problem_id = ?", (PID,))
        t.store.conn.commit()
    try:
        parts = call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": b1, "by": "me"}, "b2": {"code": "return []", "by": "me"}})[1]["parts"]
        assert parts[0][1].startswith(server.starter_of(server.PROBLEMS[PID], "python").splitlines()[0]) and text(parts).endswith("    return []"), parts
    finally:
        with server.tutor() as t:
            t.store.conn.execute("UPDATE solution SET verified = ? WHERE problem_id = ?", (int(bool(verified)), PID))
            t.store.conn.commit()
    for bad in ([1], {"b1": {"code": 1, "by": "me"}}):
        assert refuses("/api/compose", id=PID, blocks=bad)


def found(**body) -> dict:
    """입출력 예에서 찾은 케이스(다른 방식으로 찾은 수 other는 따로 본다)."""
    return {key: value for key, value in call("/api/problems/cases", **body)[1].items() if key != "other"}


def refuses(path: str, **body) -> str:
    try:
        call(path, **body)
    except server.Refuse as exc:
        assert exc.status == 400, (path, exc.status)
        return str(exc)
    raise AssertionError(f"{path} {body} 거절해야 한다")


def checks() -> None:
    """입력 검증: 코드·키·블록·케이스·테마의 형, 불리언은 정확히 true일 때만."""
    for bad in (123, "a\0b", "x = '\ud800'"):
        assert refuses("/api/run", id=PID, code=bad)
    assert refuses("/api/code", id=PID, code="\0") == "코드에 쓸 수 없는 글자가 있어요."
    assert refuses("/api/language", id=PID, language="javascript", code=["x"])
    for bad in ("x" * 401, "sk-a\nb", ["sk"], None):
        assert refuses("/api/key", name="openai", value=bad)
    assert refuses("/api/key", name=["openai"], value="sk") and refuses("/api/key", name="openrouter", value="sk")  # 걷어 낸 공급자의 키는 받지 않는다
    for bad in ([1], {"b1": {"code": 1, "by": "me"}}, {"b1": "x = 1"}):
        assert refuses("/api/blocks", id=PID, blocks=bad)
    for bad in ("[1]", [1], [{"input": "[1]", "expected": "NaN"}], [{"input": "[1]", "expected": "[Infinity]"}]):
        assert refused({**GOOD, "cases": bad}).startswith("case-")
    assert refuses("/api/theme", theme=["talk"]) and refuses("/api/theme", theme="talk", tier=1)
    other = next(row for row in ROWS if row["id"] != PID)
    assert call("/api/solution", id=other["id"], force="true")[0] == 409  # 문자열 "true"는 참이 아니다


def error_lines() -> None:
    """실행 오류 글에서 고른 한 줄(언어마다)."""
    samples = {
        "Traceback (most recent call last):\n  File \"/w/s.py\", line 2, in solution\n    return 1 / 0\nZeroDivisionError: division by zero": "ZeroDivisionError: division by zero",
        "/w/solution.js:2\n    return x();\n           ^\n\nTypeError: x is not a function\n    at solution (/w/solution.js:2:12)\n    at main (/w/run.js:5:1)\n\nNode.js v24.1.0": "TypeError: x is not a function",
        "Exception in thread \"main\" java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3\n\tat Solution.solution(Solution.java:3)\n\tat FunctionRunner.main(FunctionRunner.java:9)":
            "Exception in thread \"main\" java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3",
        "panic: runtime error: index out of range [5] with length 3\n\ngoroutine 1 [running]:\nmain.solution(...)\n\t/w/main.go:4 +0x1d": "panic: runtime error: index out of range [5] with length 3",
        "thread 'main' panicked at src/main.rs:3:5:\nindex out of bounds: the len is 3 but the index is 5\nnote: run with `RUST_BACKTRACE=1`":
            "thread 'main' panicked at src/main.rs:3:5: index out of bounds: the len is 3 but the index is 5",  # Rust는 위치 줄 다음 줄이 이유다
        "libc++abi: terminating due to uncaught exception of type std::out_of_range: vector": "libc++abi: terminating due to uncaught exception of type std::out_of_range: vector",
        "terminate called after throwing an instance of 'std::out_of_range'\n  what():  vector::_M_range_check: __n (which is 5) >= this->size() (which is 3)":
            "terminate called after throwing an instance of 'std::out_of_range'",
        "boom\n    at solution (/w/solution.js:1:7)\n\nNode.js v24.1.0": "boom",  # 오류 이름이 없으면 자취가 아닌 마지막 줄
        "Node.js v24.1.0\n\tat b": "\tat b",  # 그것도 없으면 마지막 줄
    }
    for text, line in samples.items():
        assert server.error_line(text, "runtime_error") == line, (text, server.error_line(text, "runtime_error"))
    assert server.error_line("", "runtime_error").startswith("프로그램이 비정상적으로 끝났어요") and server.error_line("", "failed") == ""
    assert len(server.error_line("ValueError: " + "x" * 500)) == 300
    # 채점기 안쪽 이름(임시 폴더, 호출 파일, Go 모듈 이름)은 가리고 내 코드 파일은 '내 코드'로
    assert server.compile_head("# algoblockcheck\n/private/var/folders/x/algoblock-check-a1b2/solution.go:3:2: \"fmt\" imported and not used") == '내 코드:3:2: "fmt" imported and not used'
    assert server.compile_head("FunctionRunner.java:12: error: incompatible types\nSolution.java:6: error: ';' expected\n2 errors") == "error: incompatible types\n내 코드:6: error: ';' expected\n2 errors"
    assert server.compile_head("error: no matching function for call to 'algoblockJson'\n   49 |  std::cout << algoblockJson(solution(a0)) << 1;\n") == server.CALL_FAILED  # 호출 코드의 이름은 화면에 나오지 않는다
    assert server.compile_head("error: literal out of range for `i32`\n  --> algoblock_main.rs:44:20\n   |") == "error: literal out of range for `i32`\n   |"
    trace = 'Traceback (most recent call last):\n  File "/private/var/folders/x/algoblock-check-ab12/algoblock_runner.py", line 9, in <module>\n  File "/private/var/folders/x/algoblock-check-ab12/solution.py", line 3\nKeyError: \'l\''
    assert server.clean(trace) == 'Traceback (most recent call last):\n  File "내 코드", line 3\nKeyError: \'l\''
    # 숨은 테스트에 보일 예외 이름과 한 줄 풀이(언어마다)
    for line, name in (("IndexError: list index out of range", "IndexError"), ('Exception in thread "main" java.lang.StackOverflowError', "StackOverflowError"),
                       ('Exception in thread "main" java.lang.ArrayIndexOutOfBoundsException: Index 100000 out of bounds for length 100000', "ArrayIndexOutOfBoundsException"),
                       ("panic: runtime error: index out of range [5] with length 3", "panic"), ("thread 'main' panicked at 내 코드:3:5:", "panic"), (server.ABNORMAL, server.ABNORMAL),
                       ("thread 'main' (4242) panicked at 내 코드:3:5: index out of bounds: the len is 3 but the index is 5", "index out of bounds"),  # 숨은 테스트는 숫자를 빼고 이유만
                       ("libc++abi: terminating due to uncaught exception of type std::out_of_range: vector", "std::out_of_range"),
                       ("terminate called after throwing an instance of 'std::out_of_range'", "std::out_of_range")):
        assert server.exception_name(line) == name, line
    for text, language, words in ((trace, "python", "딕셔너리에 없는 키"), ('Exception in thread "main" java.lang.NullPointerException', "kotlin", "null인 값"),
                                  ("TypeError: x is not a function\n    at solution (/w/solution.js:2:12)", "javascript", "함수가 아닌 것"),
                                  ("panic: runtime error: index out of range [5] with length 3\n\ngoroutine 1 [running]:", "go", "슬라이스의 범위"),
                                  ("thread 'main' panicked at src/main.rs:3:5:\nattempt to subtract with overflow", "rust", "형의 범위를 넘었어요"),
                                  ("thread 'main' panicked at src/main.rs:3:5:\ncalled `Option::unwrap()` on a `None` value", "rust", "unwrap()"),
                                  ("thread 'main' panicked at src/main.rs:3:5:\nindex out of bounds: the len is 0 but the index is 9", "rust", "벡터의 범위"),
                                  ("libc++abi: terminating due to uncaught exception of type std::out_of_range: vector", "cpp", "at()으로"),
                                  ("IndexError: string index out of range", "python", "리스트나 문자열의 범위"),
                                  ("NameError: name 'heapq' is not defined", "python", "heapq를 쓰려면 맨 위에 `import heapq`처럼 적어요."),
                                  ("NameError: name 'deque' is not defined", "python", "deque을 쓰려면 맨 위에 `from collections import deque`처럼 적어요."),  # import deque가 아니다
                                  ("NameError: name 'Counter' is not defined", "python", "`from collections import Counter`"),
                                  ("NameError: name 'permutations' is not defined", "python", "`from itertools import permutations`"),
                                  ("NameError: name 'lru_cache' is not defined", "python", "`from functools import lru_cache`"),
                                  ("NameError: name 'bisect_left' is not defined", "python", "`from bisect import bisect_left`"),
                                  ("NameError: name 'heappush' is not defined", "python", "`from heapq import heappush`(또는 `import heapq` 뒤 `heapq.heappush`)처럼")):
        assert words in server.error_hint(text, language), (language, server.error_hint(text, language))
    assert server.error_hint("TypeError: x is not a function", "python").startswith("값의 형이") and server.error_hint("boom", "python") == ""
    assert "import" not in server.error_hint("NameError: name 'totl' is not defined", "python")  # 표준 모듈 이름이 아니면 덧붙이지 않는다
    assert server.compile_head("In file included from /private/var/folders/x/algoblock-check-a1/algoblock_main.cpp:1:\n                 from /private/var/folders/x/algoblock-check-a1/x.h:2,\nsolution.cpp:5:20: error: expected ';'") == "내 코드:5:20: error: expected ';'"
    for name, hint in [(name, hint) for table in server.HINTS.values() for name, hint in table.items()] + [(found.pattern, hint) for _, found, hint in server.PHRASE_HINTS]:
        assert 25 <= len(hint) <= 60 and hint.count(".") == 2, (name, hint)  # 무엇이 일어났고 무엇을 볼지, 한 문장씩


def broken_files() -> None:
    """데이터 폴더의 깨진 JSON: 원본은 .broken-*로 남기고 기본값으로 시작한다."""
    import contextlib
    import io

    folder = Path(tempfile.mkdtemp(prefix="algoblock-ui-broken-"))
    cut, empty, good = folder / "problems.json", folder / "blocks.json", folder / "prefs.json"
    cut.write_text('[{"id": "u1", "title": "잘', encoding="utf-8")
    empty.write_text("null", encoding="utf-8")
    good.write_text('{"tour_seen": true}', encoding="utf-8")
    with contextlib.redirect_stderr(io.StringIO()) as err:
        assert server.read_json(cut, []) == [] and server.read_json(empty, {}) == {} and server.read_json(good, {}) == {"tour_seen": True}
        assert server.read_json(folder / "없음.json", []) == []
    kept = sorted(path.name for path in folder.iterdir())
    assert len(kept) == 3 and kept[0].startswith("blocks.json.broken-") and kept[1] == "prefs.json" and kept[2].startswith("problems.json.broken-"), kept
    assert (folder / kept[2]).read_text(encoding="utf-8") == '[{"id": "u1", "title": "잘' and "problems.json" in err.getvalue()


def http() -> None:
    """실제 HTTP: 다른 사이트의 요청과 깨진 요청을 본문을 읽기 전에 막고, 오류는 한국어 JSON으로."""
    import contextlib
    import io
    import threading
    from http.client import HTTPConnection

    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    mine = f"http://127.0.0.1:{httpd.server_port}"

    def send(path: str, body: bytes = b"{}", headers: dict | None = None, method: str = "POST") -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", httpd.server_port, timeout=60)
        conn.request(method, path, body, {"Content-Type": "application/json", **(headers or {})})
        res = conn.getresponse()
        out = res.status, json.loads(res.read())
        conn.close()
        return out

    with contextlib.redirect_stderr(io.StringIO()) as err:
        assert send("/api/problems", headers={"Content-Type": "text/plain; x=application/json"})[0] == 415
        assert send("/api/compose", headers={"Content-Type": "text/plain"})[0] == 415  # 모으기 요청도 다른 POST와 같은 검사를 탄다
        assert send("/api/compose", headers={"Origin": "https://evil.example"})[0] == 403
        assert send("/api/problems", headers={"Origin": "https://evil.example"})[0] == 403
        assert send("/api/problems", headers={"Origin": "null"})[0] == 403
        assert send("/api/problems", headers={"Sec-Fetch-Site": "cross-site"})[0] == 403
        assert send("/api/update", b'{"action": "install"}', {"Origin": "https://evil.example"})[0] == 403  # 업데이트도 같은 검사를 탄다
        assert send("/api/problems")[0] == 200  # Origin 없음(설치본 웹뷰가 아닌 도구)
        assert send("/api/problems", headers={"Origin": mine, "Sec-Fetch-Site": "same-origin", "Content-Type": "Application/JSON; charset=utf-8"})[0] == 200  # 앱 화면
        for body in (b"{", b'{"id": "\xff"}', b"[" * 100_000, b"[]"):
            status, payload = send("/api/problems", body)
            assert (status, payload["detail"]["message"]) == (400, "요청을 읽지 못했어요."), (body[:10], status, payload)
        assert send("/api/problems", headers={"Content-Length": "twelve"})[0] == 400
        for method in ("PUT", "DELETE", "PATCH", "OPTIONS"):
            assert send("/api/problems", method=method)[0] == 405
        handle = server.handle
        server.handle = lambda path, body: 1 / 0
        try:
            status, payload = send("/api/problems")
        finally:
            server.handle = handle
    assert status == 500 and "ZeroDivision" not in json.dumps(payload) and payload["detail"]["message"].startswith("앱 안에서 문제가 생겼어요") and "ZeroDivisionError" in err.getvalue()
    httpd.shutdown()
    httpd.server_close()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def upload() -> None:
    """파일로 문제 등록: md·txt·PDF에서 글 읽기, 거절, 이미지 + AI 없음, 원본 보관·내려 주기·바꾸기·지우기."""
    import contextlib
    import io
    import threading
    from http.client import HTTPConnection
    from unittest.mock import patch

    from tutor.ingest import ocr as ocr_tool
    from tutor.llm import LlmNotConfigured
    from tutor.tests.test_ingest import text_pdf

    md, txt = {"name": "a.md", "data": b64("## 입력\n두 수".encode())}, {"name": "b.txt", "data": "data:text/plain;base64," + b64("## 출력\n합".encode())}
    NO_TABLE = [{"where": "입출력 예", "note": "입출력 예를 찾지 못했어요"}, {"where": "제한사항", "note": "수 범위를 찾지 못했어요"}]  # 읽은 글의 규칙 대조
    assert call("/api/problems/read", text=" 문제 ", files=[md, txt])[1] == {"text": "문제\n\n## 입력\n두 수\n\n## 출력\n합", "ocr": False, "doubts": NO_TABLE}  # 데이터 URL 머리도 받는다
    assert call("/api/problems/read", files=[{"name": "p.PDF", "data": b64(text_pdf("Sum two numbers"))}])[1]["text"] == "Sum two numbers"
    png = {"name": "x.png", "data": b64(b"\x89PNG\r\n\x1a\nfake")}
    for files, words in (([{"name": "a.docx", "data": b64(b"x")}], "올릴 수 없는 파일이에요(a.docx)"), ([png] * 21, "20장"),
                         ([{"name": "a.txt", "data": "%%%"}], "a.txt 파일을 읽지 못했어요"), ([{"name": "big.txt", "data": b64(b"a" * (8 * 1024 * 1024 + 1))}], "8MB까지 올릴 수 있어요: big.txt"),
                         ([{"name": "a.md", "data": b64(b"  ")}], "비었어요"), ([{"name": "a.md"}], "모양"), ("a.md", "모양"),
                         ([{"name": "a.pdf", "data": b64(text_pdf("a"))}, {"name": "b.PDF", "data": b64(text_pdf("b"))}], "PDF는 하나만 올릴 수 있어요.")):
        assert words in refuses("/api/problems/read", files=files), words

    # 원본 보관: 등록하면 실리고, 거절된 등록은 아무것도 남기지 않는다
    before = len(server.PROBLEMS)
    assert "올릴 수 없는 파일이에요" in refuses("/api/problems/new", **GOOD, files=[{"name": "a.bmp", "data": b64(b"x")}])  # 엔진은 받아도 보관 목록에 없다
    assert "20장" in refuses("/api/problems/new", **GOOD, files=[png] * 21) and len(server.PROBLEMS) == before
    pid = call("/api/problems/new", **GOOD, files=[{**png, "name": "캡처 1.png"}, md])[1]["id"]
    assert call("/api/state", id=pid)[1]["problem"]["assets"] == [{"n": 1, "name": "캡처 1.png", "type": "png"}, {"n": 2, "name": "a.md", "type": "md"}]
    assert sorted(path.name for path in (server.ASSETS / pid).iterdir()) == ["01.png", "02.md", "index.json"]  # 경로에는 사용자 이름을 쓰지 않는다
    assert call("/api/state", id=PID)[1]["problem"]["assets"] == [] and call("/api/state", id=server.register(GOOD)["id"])[1]["problem"]["assets"] == []

    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_port

    def get(path: str, host: str = "127.0.0.1"):
        conn = HTTPConnection("127.0.0.1", port, timeout=60)
        conn.request("GET", path, headers={"Host": host})
        res = conn.getresponse()
        out = res.status, dict(res.getheaders()), res.read()
        conn.close()
        return out

    def post(path: str, body: dict) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", port, timeout=60)
        conn.request("POST", path, json.dumps(body), {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"})
        res = conn.getresponse()
        out = res.status, json.loads(res.read())
        conn.close()
        return out

    status, headers, data = get(f"/asset/{pid}/1")
    assert (status, data, headers["Content-Type"], headers["X-Content-Type-Options"], headers["Content-Disposition"]) == (200, b"\x89PNG\r\n\x1a\nfake", "image/png", "nosniff", "inline")
    status, headers, data = get(f"/asset/{pid}/02")
    assert (status, headers["Content-Type"], data.decode()) == (200, "text/plain; charset=utf-8", "## 입력\n두 수")  # HTML로 해석되지 않게 글로 준다
    for path in (f"/asset/{pid}/9", f"/asset/{pid}/../{pid}/1", f"/asset/../data/tutor.db", f"/asset/{pid}/index", f"/asset/{PID}/1", f"/asset/{pid}/100", f"/asset/{pid}"):
        assert get(path)[0] == 404, path
    assert get(f"/asset/{pid}/1", host="evil.example")[0] == 403

    with contextlib.redirect_stderr(io.StringIO()):
        big = {"name": "big.txt", "data": b64(b"a" * 2_000_000)}  # 파일을 싣는 요청만 1MB를 넘어도 받는다
        assert post("/api/problems/read", {"files": [big]})[0] == 200 and server.MAX_BODY == 1_000_000  # 다른 요청의 상한(1MB)은 그대로
        # 이미지 + AI 없음: tesseract로 읽고 그렇다고 알린다. tesseract 글도 못 믿으면 연결 안내가 오고 서버는 계속 돈다
        no_ai = lambda: use_llm(FakeLlm({"ingest.transcribe": [LlmNotConfigured("없음")]}))  # noqa: E731
        with patch.object(ocr_tool, "run_ocr", return_value="## 입력 첫 줄에 두 정수 a와 b가 공백으로 주어진다"), patch.object(server, "model", no_ai):
            assert post("/api/problems/read", {"files": [png]}) == (200, {"text": "## 입력 첫 줄에 두 정수 a와 b가 공백으로 주어진다", "ocr": True, "doubts": NO_TABLE})  # AI가 없어 다시 읽지 않는다
        with patch.object(ocr_tool, "run_ocr", return_value=""), patch.object(server, "model", no_ai):
            status, body = post("/api/problems/read", {"files": [png]})
        assert (status, body["detail"]["code"], body["detail"]["message"]) == (503, "llm_not_configured", "이미지에서 글을 읽으려면 AI를 연결해야 해요. 연결하거나, 글을 직접 붙여 넣어 주세요.")
        assert post("/api/problems/read", {"files": [md]})[0] == 200

    # 수정: files가 없으면 그대로, 오면 통째로 바꾼다. 지우면 원본도 없다
    call("/api/problems/edit", id=pid, **{**GOOD, "title": "제목만"})
    assert len(call("/api/state", id=pid)[1]["problem"]["assets"]) == 2
    call("/api/problems/edit", id=pid, **GOOD, files=[txt])
    assert call("/api/state", id=pid)[1]["problem"]["assets"] == [{"n": 1, "name": "b.txt", "type": "txt"}] and get(f"/asset/{pid}/1")[2] == "## 출력\n합".encode() and get(f"/asset/{pid}/2")[0] == 404
    call("/api/problems/delete", id=pid)
    assert get(f"/asset/{pid}/1")[0] == 404 and not (server.ASSETS / pid).exists()
    httpd.shutdown()
    httpd.server_close()


def stages() -> None:
    """과정별 모델: 급과 추론 정도를 고르면 저장되고 바로 쓰인다. 빈 값은 기본값. 모르는 과정·급·정도는 거절한다.
    예전 설정(테마별 모델 이름, Grok·OpenRouter 키)은 조용히 옮기거나 버린다."""
    from tutor.llm import themes

    rows = {row["key"]: row for row in call("/api/accounts")[1]["themes"]}
    assert list(rows) == ["read", "guide", "blocks", "talk", "judge", "explain", "feedback", "debug"]
    assert {key: (row["default_tier"], row["default_effort"]) for key, row in rows.items()} == {
        "read": ("middle", "high"), "guide": ("middle", "high"), "blocks": ("middle", "high"), "talk": ("small", "low"),
        "judge": ("small", "low"), "explain": ("small", "medium"), "feedback": ("small", "medium"), "debug": ("small", "medium")}
    assert (rows["guide"]["model"], rows["guide"]["model_label"], rows["talk"]["model_label"]) == ("claude/claude-sonnet-5-5", "Sonnet 5.5", "Haiku 5.5")
    assert [tier["label"] for tier in call("/api/accounts")[1]["tiers"]] == ["Haiku 5.5", "Sonnet 5.5", "Opus 5.5"]
    got = call("/api/theme", theme="talk", tier="middle", effort="medium")[1]
    assert {row["key"]: (row["tier"], row["effort"], row["model"]) for row in got["themes"]}["talk"] == ("middle", "medium", "claude/claude-sonnet-5-5")
    assert themes.chosen("talk") == ("middle", "medium")
    assert server.read_json(server.PREFS_FILE, {})["stages"]["talk"] == {"tier": "middle", "effort": "medium"}
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):  # 연결을 바꿔도 고른 급이 그대로 간다
        assert {row["key"]: row["model_label"] for row in call("/api/accounts")[1]["themes"]}["talk"] == "Terra (GPT-6.1)"
    call("/api/theme", theme="talk", tier="", effort="")
    assert themes.chosen("talk") == themes.default("talk")
    for bad in ({"theme": "없는 과정"}, {"theme": "talk", "effort": "아주 높음"}, {"theme": "talk", "tier": "아주 큼"}, {"theme": "ingest"}):
        try:
            server.handle("/api/theme", bad)
            raise AssertionError("모르는 과정·급·정도는 거절해야 한다")
        except server.Refuse:
            pass
    assert server.read_json(server.PREFS_FILE, {})["tour_seen"]  # 과정을 저장해도 다른 설정이 남는다

    # 예전 설정: 테마별 모델 이름은 급으로 옮기고, 표에 없는 이름(Grok·OpenRouter·직접 적은 이름)은 버린다. 다음에 저장하면 새 모양만 남는다
    server.write_json(server.PREFS_FILE, {**server.read_json(server.PREFS_FILE, {}), "stages": None,
                                          "themes": {"ingest": {"model": "claude/claude-opus-5-5", "effort": ""}, "talk": {"model": "grok/grok-5", "effort": "high"}, "judge": "x"}})
    prefs = server.read_json(server.PREFS_FILE, {})
    themes.choose(prefs.get("stages") or themes.from_old(prefs.get("themes")))  # 서버를 켤 때와 같은 길
    rows = {row["key"]: row for row in call("/api/accounts")[1]["themes"]}
    assert [rows[key]["model_label"] for key in ("read", "guide", "blocks", "talk", "judge")] == ["Opus 5.5"] * 3 + ["Haiku 5.5"] * 2 and rows["talk"]["effort"] == "high"
    call("/api/theme", theme="judge", tier="", effort="")
    prefs = server.read_json(server.PREFS_FILE, {})
    assert "themes" not in prefs and prefs["stages"]["read"] == {"tier": "large", "effort": ""}
    call("/api/theme", theme="read", tier="", effort=""), call("/api/theme", theme="guide", tier="", effort=""), call("/api/theme", theme="blocks", tier="", effort=""), call("/api/theme", theme="talk", tier="", effort="")
    assert all(row["tier"] == row["default_tier"] and row["effort"] == row["default_effort"] for row in call("/api/accounts")[1]["themes"])

    # keys.json의 값이 글이 아니면 그 항목만 건너뛰고, 걷어 낸 공급자의 키(Grok·OpenRouter)는 읽지 않는다(프로젝트의 .env는 읽지 않게 바꿔 끼운다)
    server.write_json(server.KEY_FILE, {"OPENAI_API_KEY": 123, "XAI_API_KEY": "xai-test", "OPENROUTER_API_KEY": "or-test"})
    with patch.object(server, "ROOT", TMP):
        server.load_keys()
    assert not {"OPENAI_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY"} & set(os.environ)
    assert set(call("/api/accounts")[1]["keys"]) == {"claude", "openai"} and not call("/api/accounts")[1]["connected"]


def newest_models() -> None:
    """연결이 확인되면 뒤에서 모델 목록을 받아 시리즈마다 최신 이름을 쓴다. 받은 결과는 저장해 다음 실행에 쓰고, 하루에 한 번까지만 받는다. 받지 못하면 표의 이름."""
    import threading
    from app.llm.claude.api_key import messages
    from tutor.llm import themes

    asked = []

    def wait():
        for thread in [t for t in threading.enumerate() if t.name.startswith("models-")]:
            thread.join(5)

    def listing():
        asked.append(1)
        return ["claude-sonnet-5-5", "claude-sonnet-5-6", "claude-haiku-5-5", "claude-haiku-5-6-20270101"]

    def offline():
        asked.append(1)
        raise OSError("오프라인")

    import contextlib
    import io

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}), patch.object(server, "PREPARE", True), contextlib.redirect_stderr(io.StringIO()):
        with patch.object(messages, "models", offline):  # 받지 못했다: 표의 이름, 저장하지 않는다
            call("/api/accounts"), wait()
            assert asked == [1] and themes.model_of("middle") == "claude/claude-sonnet-5-5" and not server.MODELS_FILE.exists()
        server.MODEL_TRIED.clear()
        with patch.object(messages, "models", listing):
            call("/api/accounts"), wait()
            body = call("/api/accounts")[1]  # 같은 프로세스에서는 다시 받지 않는다
            assert len(asked) == 2 and {row["key"]: row["model_label"] for row in body["themes"]}["guide"] == "Sonnet 5.6", asked
            assert {row["key"]: row["model_label"] for row in body["themes"]}["talk"] == "Haiku 5.5"  # 날짜 붙은 이름은 건너뛴다
            saved = server.read_json(server.MODELS_FILE, {})["claude"]
            assert saved["names"]["sonnet"] == "claude-sonnet-5-6"
            server.MODEL_TRIED.clear()
            call("/api/accounts"), wait()
            assert len(asked) == 2  # 받은 지 하루가 안 됐다
        themes.NEWEST.clear()
        for name, row in server.read_json(server.MODELS_FILE, {}).items():  # 다음 실행: 저장한 결과를 다시 쓴다(서버를 켤 때와 같은 길)
            themes.NEWEST[name] = themes.newest(row["names"].values())
        assert themes.model_of("middle") == "claude/claude-sonnet-5-6"
    themes.NEWEST.clear()
    server.MODEL_TRIED.clear()
    server.MODELS_FILE.unlink()


def kept_languages() -> None:
    """언어마다 준비 결과를 보관한다: 언어 A → B → A에서 두 번째 A는 모델 0회(가이드·계획·해설을 되살린다). 대화 진행은 처음부터."""
    pid = server.register(GOOD)["id"]
    ready = own_ready("def solution(a, b):\n    return a + b")
    fake = FakeLlm({})
    with use_llm(fake), server.tutor() as t:
        t.adopt(pid, ready)  # python으로 준비해 둔 것(모델이 만드는 것)
        t.store.conn.execute("UPDATE tutor_session SET explain_json=? WHERE problem_id=?", ('{"sections": []}', pid))
        t.store.conn.commit()
    call("/api/turn", id=pid, mode="chair", event="start")
    call("/api/language", id=pid, language="java")
    with server.tutor() as t:
        assert t.store.load(pid).plan is None and t.store.load(pid).solution is None  # 새 언어는 새로 준비한다
        t.adopt(pid, own_ready("class Solution { int solution(int a, int b) { return a + b; } }"))
    back = call("/api/language", id=pid, language="python")[1]
    with use_llm(fake), server.tutor() as t:
        ctx = t.store.load(pid)
        assert ctx.plan is not None and ctx.solution.code == ready["solution"]["code"]
        assert t.store.conn.execute("SELECT explain_json FROM tutor_session WHERE problem_id=?", (pid,)).fetchone()[0] == '{"sections": []}'
        assert t.prepare(pid).status == 200 and not fake.calls  # 계획이 있어 미리 만들기가 모델을 부르지 않는다
        assert ctx.open_count == 1 and not ctx.chair  # 대화 진행은 처음부터
    assert back["session"]["blocks"]
    again = call("/api/language", id=pid, language="java")[1]
    with server.tutor() as t:
        assert t.store.load(pid).solution.code.startswith("class Solution")  # B도 되살린다
    call("/api/problems/edit", id=pid, title=GOOD["title"], text=GOOD["text"] + " 고침", cases=GOOD["cases"])  # 글을 고치면 보관한 것도 버린다
    assert pid not in server.read_json(server.KEPT_FILE, {})
    assert again["session"]["blocks"]
    call("/api/problems/delete", id=pid)


def own_ready(code: str) -> dict:
    """등록 문제에 손으로 넣는 준비 결과(블록 하나가 코드 전체)."""
    lines = code.splitlines()
    return {"fact": {"spec": "두 수의 합", "patterns": [], "skills": [], "size": 0},
            "solution": {"approach": "더한다.", "steps": ["더한다"], "code": code, "verified": True, "clues": []},
            "plan": {"strategy": "fresh", "score": None, "algorithm": "implementation", "out_of_scope": False, "link": "",
                     "blocks": [{"id": "b1", "kind": "var_during", "name": "더하기", "goal": "두 수를 더한다", "reference": code, "lines": [1, len(lines)], "checks": ["더한다"],
                                 "hints": ["무엇을 돌려줘야 할까요?", "'합'은 무엇일까요?", "1과 2라면 무엇을 돌려주나요?"]}]}}


def edit_changes() -> None:
    """등록 문제를 고치면 바뀐 만큼만 다시 준비한다(모델 0회인 길): 공백만 다른 글과 케이스만 바꾼 저장은 준비를 그대로 두고,
    케이스가 가이드 코드를 떨어뜨리면 가이드·계획만 지우고(뼈대는 남김), 글을 고치면 처음부터 다시 준비한다."""
    pid = server.register(GOOD)["id"]
    with server.tutor() as t:
        t.adopt(pid, own_ready("def solution(a, b):\n    return a + b"))
    redo = []

    def kept() -> tuple[bool, bool]:
        with server.tutor() as t:
            ctx = t.store.load(pid)
            return ctx.plan is not None, bool(ctx.spec)

    with patch.object(server, "prepare_later", redo.append):
        call("/api/problems/edit", id=pid, title=GOOD["title"], text="  두 수 a, b의 합을\nreturn 하도록   solution 함수를 완성하세요. ", cases=GOOD["cases"])  # 공백·줄바꿈만
        assert kept() == (True, True) and redo == []
        assert call("/api/state", id=pid)[1]["problem"]["text"].startswith("두 수 a, b의 합을\nreturn")  # 고친 글은 저장한다
        call("/api/problems/edit", id=pid, title=GOOD["title"], text=GOOD["text"], cases=[*GOOD["cases"], {"input": "[7, 8]", "expected": "15", "hidden": True}])  # 케이스만, 가이드 통과
        assert kept() == (True, True) and redo == []
        call("/api/problems/edit", id=pid, title=GOOD["title"], text=GOOD["text"], cases=[{"input": "[1, 1]", "expected": "3"}])  # 케이스만, 가이드가 떨어진다
        assert kept() == (False, True) and redo == [pid]
        with server.tutor() as t:
            t.adopt(pid, own_ready("def solution(a, b):\n    return a + b + 1"))
        call("/api/problems/edit", id=pid, title=GOOD["title"], text=GOOD["text"] + " 정수만", cases=[{"input": "[1, 1]", "expected": "3"}])  # 글을 고쳤다
        assert kept() == (False, False) and redo == [pid, pid]
    call("/api/problems/delete", id=pid)


def read_check() -> None:
    """읽기 검증: 읽은 글을 규칙과 글자 읽기로 대조해, 어긋나면 그 장만 한 번 다시 읽고(모델 1회) 남은 곳을 doubts로 준다."""
    from tutor.ingest import ocr as ocr_tool

    png = {"name": "p.png", "data": b64(b"\x89PNG")}
    good = ("정수 a, b의 합을 return 하도록 solution 함수를 완성하세요.\n\n제한사항\n- a, b는 1 이상 1,000 이하입니다.\n\n"
            "| a | b | result |\n|---|---|---|\n| 1 | 2 | 3 |\n| 5 | 5 | 10 |")
    half = good.replace("| 5 | 5 | 10 |", "| 5 | 10 |")  # 표가 반쪽만 읽혔다(그 줄의 인자 수가 머리와 다르다)
    fake = FakeLlm({"ingest.transcribe": [{"readable": True, "text": half}, {"readable": True, "text": good}]})
    with use_llm(fake), patch.object(ocr_tool, "run_ocr", return_value=""):  # 글자 읽기 없음
        got = call("/api/problems/read", files=[png])[1]
    assert (got["text"], got["doubts"], len(fake.calls)) == (good, [], 2), got  # 그 장을 한 번 다시 읽어 바로잡았다
    fake = FakeLlm({"ingest.transcribe": [{"readable": True, "text": half}, {"readable": True, "text": half}]})
    with use_llm(fake), patch.object(ocr_tool, "run_ocr", return_value=good.replace("1,000", "100")):  # 글자 읽기는 1,000을 100으로 읽었다
        got = call("/api/problems/read", files=[png])[1]
    assert got["doubts"] == [{"where": "입출력 예", "note": "읽지 못한 줄이 1개 있어요(표의 제목 줄과 칸 수가 다르거나 값을 읽지 못했어요)"},
                             {"where": "1번째 장", "ai": "1000", "ocr": "100"}], got["doubts"]
    assert len(fake.calls) == 2  # 다시 읽기는 한 번만
    fake = FakeLlm({"ingest.transcribe": [{"readable": True, "text": good.replace("1 이상 1,000 이하", "작은 수")}] * 2})
    with use_llm(fake), patch.object(ocr_tool, "run_ocr", return_value=""):
        assert call("/api/problems/read", files=[png])[1]["doubts"] == [{"where": "제한사항", "note": "수 범위를 찾지 못했어요"}]


def cross_cases() -> None:
    """등록한 문제의 풀이 대조(실제 채점기 + 가짜 모델): 정답 풀이와 단순 풀이가 생성기의 입력에서 맞으면 숨은·효율성 케이스가 생겨
    틀린 풀이와 느린 풀이가 떨어진다. 제한사항을 어긴 입력은 버린다. 생성기는 채점기 프로세스로만 돈다(앱의 exec·eval에 오지 않고, 앱의 환경 변수를 보지 못한다)."""
    import builtins

    import casemake
    from tutor.state import Bound

    text = ("정수 배열 numbers의 모든 원소의 합을 return 하도록 solution 함수를 완성하세요.\n\n제한사항\n"
            "- numbers의 길이는 1 이상 100,000 이하입니다.\n- 원소는 -1,000 이상 1,000 이하입니다.")
    pid = server.register({"title": "배열의 합", "text": text, "cases": [{"input": "[[1, 2, 3]]", "expected": "6"}]})["id"]
    code = "def solution(a):\n    total = 0\n    for number in a:\n        total += number\n    return total"  # 시작 코드의 머리(표 머리 이름이 없어 a)를 따른다
    maker = ("import os\nimport random\nassert not any(name.startswith('ALGOBLOCK_') for name in os.environ)  # I1_MAKER\n"
             "def small():\n    return [[[random.randint(-1000, 1000) for _ in range(random.randint(1, 8))]] for _ in range(20)] + [[[5000]]]\n"
             "def edge():\n    return [[[-1000]], [[1000] * 8], [[0]]]\n"
             "def large():\n    return [[[random.randint(-1000, 1000) for _ in range(100000)]]]\n")
    bounds = [{"arg": 0, "low": -1000, "high": 1000, "shortest": 1, "longest": 100000}]
    hints = ["무엇을 돌려줘야 할까요?", "'모든 원소의 합'은 무엇을 더하라는 걸까요?", "[1, 2, 3]이라면 무엇을 돌려주나요?"]
    draft = {"algorithm": "implementation", "out_of_scope": False, "blocks": [{"id": "b1", "kind": "var_during", "name": "더하기", "goal": "모두 더한다", "lines": [1, 5], "checks": ["더한다"], "hints": hints}]}
    fake = FakeLlm({"plan.solve": [{"clues": [], "approach": "하나씩 더한다.", "steps": ["더한다 — 합"], "code": code}],
                    "plan.brute": [{"code": "```python\ndef solution(numbers):\n    return sum(numbers)\n```"}],
                    "plan.cases": [{"code": maker, "bounds": bounds}], "plan.draft_blocks": [draft]})
    seen, real_exec, real_eval = [], builtins.exec, builtins.eval

    def watch(run):
        def inner(source, *args, **kwargs):
            seen.append(source if isinstance(source, str) else str(getattr(source, "co_consts", "")))
            return run(source, *args, **kwargs)
        return inner

    with use_llm(fake), patch("builtins.exec", watch(real_exec)), patch("builtins.eval", watch(real_eval)):
        with server.tutor() as t:
            t.store.put_fact(pid, "정수 배열의 합", [])
            assert t.prepare(pid).status == 200
    assert not [one for one in seen if "I1_MAKER" in one or "return sum(numbers)" in one]  # 모델이 쓴 코드는 앱 프로세스에서 돌지 않았다
    made = [case for case in server.PROBLEMS[pid].cases if case.get("made")]
    hidden = [case for case in made if case["kind"] == "accuracy"]
    assert 5 <= len(hidden) <= casemake.HIDDEN_MAX and sum(case["kind"] == "efficiency" for case in made) == 1, made
    assert not [case for case in hidden if "5000" in case["input"]]  # 제한사항(원소 1,000 이하)을 어긴 입력은 버렸다
    row = next(row for row in call("/api/problems")[1]["problems"] if row["id"] == pid)
    assert (row["verified"], row["verified_name"], row["check"]["hidden"], row["check"]["efficiency"], row["check"]["calls"], row["check"]["tiers"]) == (
        "all", "예시와 자동 테스트 모두 통과", len(hidden), 1, 2, ["middle"]), row
    state = call("/api/state", id=pid)[1]["problem"]
    assert len(state["own_cases"]) == 1 and state["cases"] == {"example": 1, "accuracy": len(hidden), "efficiency": 1}  # 수정 화면에는 내가 넣은 케이스만
    wrong = "def solution(numbers):\n    if len(numbers) == 1:\n        return 0\n    return sum(numbers)"  # 공개 예시는 통과한다
    slow = "def solution(numbers):\n    total = 0\n    for i in range(len(numbers)):\n        for j in range(i + 1):\n            total += 0\n    return sum(numbers)"
    assert call("/api/submit", id=pid, code=wrong)[1]["ok"] is False
    result = call("/api/submit", id=pid, code=slow)[1]
    assert not result["ok"] and [case["status"] for case in result["cases"] if case["kind"] == "efficiency"] == ["timeout"], result["status"]
    assert call("/api/submit", id=pid, code=code)[1]["ok"] is True
    # 단순 풀이와 다른 풀이: 다른 입력과 두 결과를 준다
    other = casemake.make("python", "function", wrong, "def solution(numbers):\n    return sum(numbers)", maker, [Bound(**b) for b in bounds], 1)
    assert other["status"] == "differ" and other["want"] != other["got"] and not other.get("slow"), other
    broken = casemake.make("python", "function", code, "def solution(numbers):\n    return sum(numbers)", "def small():\n    return 1 / 0\n", [Bound(**b) for b in bounds], 1)
    assert broken == {"status": "error", "why": casemake.NOT_MADE}, broken  # 화면에 보이는 까닭은 한 문장이다(함수 이름·오류 상태·자취가 없다)
    with patch.dict(os.environ, {"ALGOBLOCK_UI_CLIENT": ""}):
        assert call("/api/accounts")[1]["dev"] is False  # 개발용 연결을 고르는 칸은 개발용 연결로 띄웠을 때만 있다
    with patch.dict(os.environ, {"ALGOBLOCK_UI_CLIENT": "cli"}):
        assert call("/api/accounts")[1]["dev"] is True
    # 화면이 숨긴 선택지를 요청으로 고르지도 못한다: 개발용으로 띄우지 않았으면 'cli'를 거절한다
    saved_client = server.STATE["client"]
    try:
        with patch.dict(os.environ, {"ALGOBLOCK_UI_CLIENT": ""}):
            try:
                call("/api/client", client="cli")
                raise AssertionError("거절해야 한다")
            except server.Refuse as exc:
                assert (exc.status, exc.code) == (403, "dev_only") and server.STATE["client"] == saved_client, (exc.status, exc.code)
            assert call("/api/client", client="provider")[1]["client"] == "provider"
        with patch.dict(os.environ, {"ALGOBLOCK_UI_CLIENT": "cli"}):
            assert call("/api/client", client="cli")[1]["client"] == "cli"
    finally:
        server.STATE["client"] = saved_client
    # 표준 입출력 방식도 같은 길: 생성기는 입력 글을, 두 풀이는 출력 글을 낸다
    gen = ("import random\ndef small():\n    out = []\n    for _ in range(10):\n        xs = [random.randint(-9, 9) for _ in range(random.randint(1, 5))]\n"
           "        out.append(f'{len(xs)}\\n' + ' '.join(map(str, xs)) + '\\n')\n    return out\ndef edge():\n    return ['1\\n-1000\\n', '1\\n-5000\\n']\n"
           "def large():\n    return ['100000\\n' + ' '.join(['1000'] * 100000) + '\\n']\n")
    fast = "import sys\ndata = sys.stdin.read().split()\nprint(sum(map(int, data[1:])))"
    same = casemake.make("python", "program", fast, "n = int(input())\nprint(sum(int(x) for x in input().split()))", gen, [Bound(arg=0, low=-1000, high=100000)])
    assert (same["status"], len(same["hidden"]), len(same["large"]), same["dropped"]) == ("same", 11, 1, 1), str(same)[:300]  # -5000은 범위 밖이라 버렸다
    assert same["hidden"][0] == ("1\n-1000\n", "-1000\n"), same["hidden"][0]
    # 단계를 고치고 글을 고치면 만든 케이스와 결과를 버린다(다음 준비가 다시 만든다)
    call("/api/problems/edit", id=pid, title="배열의 합", text=text, cases=[{"input": "[[1, 2, 3]]", "expected": "6"}], level=3)
    row = next(row for row in call("/api/problems")[1]["problems"] if row["id"] == pid)
    assert (row["level"], row["level_by"], row["verified"]) == (3, "user", "all"), row
    with patch.object(server, "prepare_later", lambda pid: None):
        call("/api/problems/edit", id=pid, title="배열의 합", text=text + " 빈 배열은 없습니다.", cases=[{"input": "[[1, 2, 3]]", "expected": "6"}])
    assert not [case for case in server.PROBLEMS[pid].cases if case.get("made")] and not (server.LARGE / pid).exists()
    assert next(row for row in call("/api/problems")[1]["problems"] if row["id"] == pid)["verified"] == ""
    call("/api/problems/delete", id=pid)


def build_only() -> None:
    """묶기 도구: --only는 고른 문제만 새로 만들고 다른 행은 지금 묶음 그대로 두며, 없는 폴더는 2로 끝난다. 기본은 다른 언어 풀이도 싣는다(--no-langs로만 뺀다)."""
    out = TMP / "only.json"
    out.write_text(json.dumps([row for row in ROWS if row["id"] != FIRST["id"]], ensure_ascii=False), encoding="utf-8")  # 고른 문제만 빠진 묶음
    run = lambda *more: subprocess.run([sys.executable, str(HERE / "make_builtin.py"), "build", "--no-model", "--no-check", "--out", str(out), *more], capture_output=True, text=True)
    done = run("--only", "hash/1_popular_shelf")
    assert done.returncode == 0, done.stderr
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert len(rows) == len(ROWS) and {row["id"] for row in rows} == {row["id"] for row in ROWS}, len(rows)
    assert len(next(row for row in rows if row["id"] == FIRST["id"])["languages"]) > 1  # 기본은 다른 언어 풀이도 싣는다
    assert run("--only", "hash/1_popular_shelf", "--no-langs").returncode == 0
    assert next(row for row in json.loads(out.read_text(encoding="utf-8")) if row["id"] == FIRST["id"])["languages"] == ["python"]
    assert run("--only", "hash/없는_폴더").returncode == 2 and run("--only").returncode == 2


def main() -> None:
    build_only()
    error_lines()
    broken_files()
    fake = FakeLlm({})
    with use_llm(fake):
        assert not call("/api/accounts")[1]["connected"]  # 키가 없다: 아래는 모두 AI 없이 돈다
        registered()
        bundle()
        limits()
        builtin(fake)
        compose()
        report()
        home()
        own_theme()
        debug_pass()
        own_way_flow()
        chair_found()
        language_memory()
        no_tool()
        results()
        tools()
        edit_delete()
        checkpoints()
        prep_failed()
        stale_save()
        builtin_prepare()
        own_guide()
        kept_languages()
        edit_changes()
        explicit_mode()
        program_mode()
        program_tutor()
        own_starter()
        case_shapes()
        table()
        hidden_cases()
        assert not fake.calls, fake.calls  # 고치기·지우기도 모델을 부르지 않는다
        checks()
        http()
        upload()
        assert not fake.calls, fake.calls  # 파일 읽기와 원본 보관도 모델을 부르지 않는다
    try:
        call("/api/key", name="PATH", value="x")
        raise AssertionError("아무 환경 변수나 바꾸게 두면 안 된다")
    except server.Refuse:
        pass
    assert not call("/api/accounts")[1]["tour_seen"]  # 처음 안내는 한 번 닫으면 다시 뜨지 않는다
    assert call("/api/tour")[1]["tour_seen"] and call("/api/accounts")[1]["tour_seen"]
    for path, (name, _) in server.STATIC.items():  # 화면이 부르는 파일이 모두 있다(글꼴 포함)
        assert (server.STATIC_DIR / name).is_file(), path

    import test_update  # 업데이트(가짜 네트워크, 임시 폴더의 가짜 앱)
    test_update.run()
    status = call("/api/update", action="status")[1]  # 소스 실행: 확인만 하고 받기·바꾸기는 하지 않는다
    assert status["current"] == server.updater.VERSION and status["frozen"] is False and status["installable"] is False, status
    try:
        call("/api/update", action="download")
        raise AssertionError("받을 새 버전이 없으면 거절한다")
    except server.Refuse as exc:
        assert exc.status == 409
    stages()
    newest_models()
    read_check()
    cross_cases()

    import threading  # 첫 요청 여럿이 함께 와도 색인은 한 번만 연다(둘째가 실패해 검색이 꺼진 채 남지 않게)
    gate = threading.Barrier(4)
    threads = [threading.Thread(target=lambda: (gate.wait(), server.index())) for _ in range(4)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    assert len(server.INDEX) == 1, server.INDEX
    if server.INDEX[0] is not None:
        server.INDEX[0].close()
    print("ok")


if __name__ == "__main__":
    main()
