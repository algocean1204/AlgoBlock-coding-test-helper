"""화면 서버 확인. 모델을 부르지 않는다(등록 검사, 채점, 언어, 힌트, 해설, 학습 보고서, 처음부터, 파일로 등록).

실행: cd app && uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/test_server.py
기본 문제는 ui/problems에서 지금 검사를 통과해 있는 것(cases.json이 있는 폴더)을 임시 파일로 묶어 쓴다. ui/builtin.json은 건드리지 않는다.
"""

import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
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

server.ROOT = TMP  # 저장소의 .env를 읽지 않는다(키 지우기 흐름이 load_keys를 다시 불러도 진짜 키가 환경에 올라오지 않게)
from tutor.common.scope import ALGORITHMS  # noqa: E402
from tutor.common.talk_rules import MANY_ANSWERS  # noqa: E402
from tutor.llm import FakeLlm, use_llm  # noqa: E402

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
    assert ran["notice"] == ""
    judge_common, real = server.check_judge().common, server.check_judge().common.run_command
    with patch.object(judge_common, "run_command", lambda *a, **k: {**real(*a, **k), "warning": "작업 없음", "warning_kind": "no_job"}):  # Windows에서 작업 객체를 쓰지 못한 실행
        warned, own = call("/api/run", id=pid, code=right)[1], call("/api/run", id=pid, code=right, input="[1, 2]")[1]
    assert warned["ok"] and (warned["notice"], own["notice"]) == (server.NO_LIMITS, server.NO_LIMITS), (warned, own)  # 화면에 한 줄로 알린다
    assert "커밋 메모리 상한" in server.NO_LIMITS and "채점 결과는 그대로" in server.NO_LIMITS
    stuck = {"status": "runtime_error", "stdout": "", "stderr": "", "time_ms": 0, "warning": "재개 안 됨", "warning_kind": "not_started"}
    with patch.object(judge_common, "run_command", lambda *a, **k: stuck):  # 멈춘 채 만든 제출 코드를 시작하지 못한 실행
        failed = call("/api/run", id=pid, code=right)[1]
    assert not failed["ok"] and failed["notice"] == server.NOT_STARTED and "채점 결과는 그대로" not in server.NOT_STARTED, failed
    assert call("/api/submit", id=pid, code=right)[1]["ok"]
    assert call("/api/debug", id=pid, code=right)[1]["passed"]  # 통과한 코드는 디버깅으로 가지 않는다(모델 0회)
    state = call("/api/state", id=pid, mode="chair")[1]["problem"]
    assert (state["passed"], state["submitted"], state["code"], state["language"]) == (1, 2, right, "python")  # run은 제출로 세지 않는다. 같은 코드는 한 번만 센다
    assert len(state["languages"]) == 5 and state["starter"].startswith("def solution(a, b):") and state["cases"] == {"example": 2, "accuracy": 0, "efficiency": 0}

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
    assert problem["study"] == {"hints_seen": 0, "hints_total": 6, "solution_seen": False, "solution_open": False, "has_guide": True, "passed_now": False, "unaided_open": True}
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
    held = server.REPORTS[PID][1]["cases"]  # 들고 있는 결과에는 큰 입력 글이 없다(문제마다 수 MB)
    assert any(case["kind"] == "efficiency" for case in held) and all(case["input"] == "" for case in held if case["kind"] == "efficiency")
    assert timed["status"] == "timeout" and timed["score"]["accuracy"][0] == timed["score"]["accuracy"][1] and timed["score"]["efficiency"][0] < 2
    debug = call("/api/debug", id=PID, code=slow)[1]
    assert debug["efficiency_only"] and not debug["passed"]  # 틀린 줄을 찾을 일이 아니다(모델 0회)
    assert "시간이 모자라요" in debug["message"] and "틀린 줄" not in debug["message"]
    deep = ("def solution(loans, k):\n    count = {}\n    shelf = []\n    def go(i):\n        if i == len(loans):\n            return\n        count[loans[i]] = count.get(loans[i], 0) + 1\n"
            "        if count[loans[i]] == k:\n            shelf.append(loans[i])\n        go(i + 1)\n    go(0)\n    return shelf\n")
    sent = []  # 답은 맞지만 큰 입력에서 재귀가 너무 깊다(제출로 남기지 않는 채점): 시간 이야기가 아니라 틀린 곳 찾기로 그 케이스를 넘긴다
    with patch.object(server.Tutor, "debug", lambda self, pid, code, report, text=None: sent.append(report) or SimpleNamespace(status=200, body={"messages": []})):
        got = call("/api/debug", id=PID, code=deep)[1]
    crashed = got["judged"]
    assert crashed["score"]["accuracy"][0] == crashed["score"]["accuracy"][1] and any(c["kind"] == "efficiency" and c["status"] == "runtime_error" for c in crashed["cases"]), crashed
    assert "efficiency_only" not in got and sent[0]["status"] == "runtime_error", sent
    assert any(c["kind"] == "efficiency" and c["status"] == "runtime_error" and c["input"] == "(아주 큰 입력)" for c in sent[0]["cases"]), sent  # 큰 입력은 싣지 않는다

    toc = [{"block": 1, "kind": "loop", "seen": 0, "total": 3}, {"block": 2, "kind": "condition", "seen": 0, "total": 3}]  # 힌트 목차: 이름은 그 블록의 힌트를 다 본 뒤에만
    assert call("/api/hint", id=PID, peek=True)[1] == {"seen": 0, "total": 6, "done": False, "shown": [], "blocks": toc}  # 들여다보기만 하면 새 힌트가 열리지 않는다
    hints = [call("/api/hint", id=PID)[1] for _ in range(7)]
    assert len(call("/api/hint", id=PID, peek=True)[1]["shown"]) == 6
    assert [(h["block"], h["step"]) for h in hints] == [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (2, 3)]
    assert [b.get("name") for b in hints[-1]["blocks"]] == ["개수 세기", "k번째에 꽂기"]  # 블록을 고르지 않으면 전처럼 블록 1부터 차례로
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
    assert study == {"hints_seen": 6, "hints_total": 6, "solution_seen": True, "solution_open": True, "has_guide": True, "passed_now": True, "unaided_open": False}
    with server.tutor() as t:
        assert t.store.study(PID)["solution_before_pass"] and t.store.study(PID)["help_first_at"] and [sub["status"] for sub in t.store.submissions() if sub["problem_id"] == PID] == ["failed", "timeout", "passed"]

    # 처음부터 해도 같은 블록으로 다시 바로 시작된다(정석 계획은 남기고 첫 블록으로만 돌린다)
    call("/api/reset", id=PID)
    assert call("/api/turn", id=PID, mode="chair", event="start")[1]["messages"][0]["text"] == first["messages"][0]["text"]

    # 언어를 바꾸면 그 언어의 시작 코드가 오고, 블록 계획은 지워진다(그 언어의 정답 풀이로 다시 짠다). 파이썬으로 돌아오면 미리 만든 계획이 다시 온다
    js = call("/api/language", id=PID, language="javascript")[1]
    assert js["problem"]["language"] == "javascript" and js["problem"]["starter"].startswith("function solution(loans, k)") and js["session"]["blocks"] == []
    assert server.given(PID, "javascript")["code"] == JS and server.given(PID, "javascript")["approach"] and server.given(PID, "cobol") is None
    if server.check_judge().judge("javascript", JS, [{"id": "1", "input": "[[\"a\"], 2]", "expected": "[]"}], mode="function")["status"] != "toolchain_missing":
        assert call("/api/submit", id=PID, code=JS)[1]["ok"]
        assert call("/api/solution", id=PID)[1]["language"] == "javascript"
    else:
        assert call("/api/submit", id=PID, code=JS)[1]["status"] == "toolchain_missing"
    assert len(call("/api/language", id=PID, language="python")[1]["session"]["blocks"]) == 2
    with server.tutor() as t:  # 돌아온 계획은 그 언어로 쓰던 코드가 있어도 다시 짜지 않고 그대로 시작한다
        t.store.update_code(PID, CODE)
        assert call("/api/turn", id=PID, mode="chair", event="start")[1]["messages"][0]["text"]
        t.store.update_code(PID, "")
    assert not fake.calls, fake.calls  # 여기까지 모델을 한 번도 부르지 않았다


def report() -> None:
    """학습 보고서의 수치가 넣은 제출 기록과 맞는다. 출석은 /api/problems가 오늘을 한 번만 찍는다."""
    call("/api/problems")
    body = call("/api/report")[1]
    assert body["attendance"]["days"] == 1 and len(body["attendance"]["recent"]) == 14 and body["attendance"]["recent"][-1] is True and not any(body["attendance"]["recent"][:-1])
    hash_ = next(theme for theme in body["themes"] if theme["key"] == "hash")
    assert (hash_["solved"], hash_["level_reached"], hash_["first_try"], hash_["solution_before_pass"], hash_["hints"]) == (1, 1, 0, 1, 6), hash_  # 본 힌트 수는 '처음부터' 뒤에도 누적이다
    assert hash_["fails"] == {"failed": 1, "runtime_error": 0, "timeout": 1, "compile_error": 0} and hash_["submissions"] >= 3 and hash_["state"] in ("progress", "weak")
    assert sum(row["unaided"] for row in body["themes"]) == body["readiness"]["solved"] and all(row["unaided"] <= row["solved"] for row in body["themes"])  # 주제별 '도움 없이'의 합 = 준비도의 수
    short = body["readiness"]["rule_short"]  # 한 문장이 '그 밖의 통과' 셋(도움을 쓴 것, 제출이 많은 것, 처음부터 뒤 하루 안)을 모두 말한다. 숫자는 상수에서 나온다
    assert all(word in short for word in ("힌트·튜터·해설을 썼거나", f"제출이 {server.UNAIDED_MAX_SUBMITS}번을 넘었거나", f"'처음부터' 뒤 {server.REPEAT_GAP_HOURS}시간 안에", "'그 밖의 통과'")) and "도움 받아 통과" not in short
    assert body["summary"]["solved"] == 1 and body["summary"]["total"] == len(ROWS) and body["summary"]["languages"]["python"] >= 5
    assert body["recent"][0]["id"] == PID and len(body["recent"]) <= 10
    assert [group["key"] for group in body["signals"]] == ["hash"] and body["signals"][0]["items"][0]["title"] == FIRST["title"]  # 푼 문제의 신호만
    assert 1 <= len(body["next"]) <= 5 and body["readiness"]["solved"] == 0
    again = [row for row in body["next"] if row["id"] == PID]  # PID는 해설을 먼저 보고 통과해서 도움 없이 푼 것이 아니다: 다시 풀 후보로 권하되 '이어서 풀기'라 하지 않는다
    assert all(row["why"].startswith("도움 없이 다시 풀기(") for row in again), again
    others = [theme for theme in body["themes"] if theme["key"] != "hash"]
    assert all(theme["state"] == "new" for theme in others)
    # 약점 규칙: 한 주제의 두 문제에서 답은 맞았지만 큰 입력에서 시간이 모자라면 약한 주제다. 한 문제에서 여러 번, 정확성 케이스의 시간 초과, 세부가 없는 예전 기록은 아니다
    other, other2 = [row for row in ROWS if row["theme"] == next(r["theme"] for r in ROWS if r["theme"] != "hash")][:2]
    with server.tutor() as t:
        for row in (other, other2):
            t.store.put_problem(row["id"], "python", row["text"], title=row["title"])
        for n in range(3):
            t.store.add_submission(other["id"], f"느린 코드 {n}", False, status="timeout", detail={"accuracy": [8, 8], "efficiency": [0, 2]})
        t.store.add_submission(other2["id"], "끝나지 않는 코드", False, status="timeout", detail={"accuracy": [2, 8], "efficiency": [0, 2]})
        t.store.add_submission(other2["id"], "예전 느린 코드", False, status="timeout")
    assert "시간이 모자랐어요" not in next(row for row in call("/api/report")[1]["themes"] if row["key"] == other["theme"])["why"]
    with server.tutor() as t:
        t.store.add_submission(other2["id"], "느린 코드", False, status="timeout", detail={"accuracy": [8, 8], "efficiency": [1, 2]})
    weak = call("/api/report")[1]["weaknesses"]
    assert weak and weak[0]["key"] == other["theme"] and weak[0]["why"].startswith("2문제에서 답은 맞았지만 큰 입력에서 시간이 모자랐어요.") and weak[0]["next"]["id"].startswith(other["theme"])
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


BANNED = ("준비됐", "합격", "약해요", "부족해요", "%")  # 준비도·실패 꼴의 말에 쓰지 않는 것
EARLY, LATE = "2000-01-01T00:00:00+09:00", "2999-01-01T00:00:00+09:00"


def history(*steps, listed: bool = False) -> dict:
    """빈 기록 파일에 steps(t를 받는 함수)를 넣고 학습 보고서를 받는다(다른 시험의 기록과 섞이지 않는다). listed면 문제 목록의 주제별 '다음'을 보고서의 themes에 겹쳐 돌려준다."""
    with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "report.db"):
        with server.tutor() as t:
            for step in steps:
                step(t)
        body = call("/api/report")[1]
        return {**body, "listed": {row["key"]: row["next"] for row in call("/api/problems")[1]["themes"]}} if listed else body


def at(when: str):
    """저장소의 지금 시각을 when으로 고정한다(제출·도움·'처음부터'를 서버의 함수 그대로 부르되 차례를 정한다)."""
    return patch("tutor.store.sqlite.now", lambda: when)


def moment(n: int, hours: int = 9) -> str:
    """시험의 시각: 2001-01-01 00:00(+09:00)부터 n초 뒤를 시간대 hours로 적은 것."""
    from datetime import datetime, timedelta, timezone
    return (datetime(2001, 1, 1, tzinfo=timezone(timedelta(hours=9))) + timedelta(seconds=n)).astimezone(timezone(timedelta(hours=hours))).isoformat()


def chat(t, pid: str, when: str) -> None:
    t.store.conn.execute("INSERT INTO message(problem_id, mode, thread, role, text, at) VALUES(?, 'chair', 'main', 'user', '질문', ?)", (pid, when))
    t.store.conn.commit()


def record(pid: str, *events):
    """문제 하나의 기록을 차례대로: (종류, 시각). 종류는 fail·pass(제출), help(튜터 기능·힌트·해설), talk(대화), reset('이 문제 처음부터')."""
    def step(t):
        t.store.put_problem(pid, "python", "글", title=pid)
        for kind, when in events:
            with at(when):
                if kind in ("fail", "pass"):
                    t.store.add_submission(pid, "코드", kind == "pass", status="passed" if kind == "pass" else "timeout",
                                           detail={"accuracy": [4, 4], "efficiency": [2, 2] if kind == "pass" else [0, 2]})
                elif kind == "help":
                    t.store.mark_help(pid)
                elif kind == "reset":
                    server.reset(t, pid)
                else:
                    chat(t, pid, when)
    return step


def solve(pid: str, first_ok: bool = True, talk: str = "", fails: int = 0, detail: bool = True, helped: str = "", **study):
    """문제 하나를 푼 기록: 틀린 제출 fails번(정확성은 맞고 큰 입력에서 시간 초과) 뒤 통과. talk는 튜터와 처음 말한 시각, helped는 도움을 쓴 시각, study는 학습 기록."""
    def step(t):
        t.store.put_problem(pid, "python", "글", title=pid)
        for n in range(fails + (not first_ok)):
            t.store.add_submission(pid, f"느린 코드 {n}", False, status="timeout", detail={"accuracy": [4, 4], "efficiency": [0, 2]} if detail else None)
        t.store.add_submission(pid, "맞은 코드", True, status="passed", detail={"accuracy": [4, 4], "efficiency": [2, 2]} if detail else None)
        if talk:
            chat(t, pid, talk)
        if helped:
            with at(helped):
                t.store.mark_help(pid)
        if study:
            t.store.set_study(pid, **study)
    return step


def fail(pid: str, status: str, detail: dict | None, language: str = "python"):
    def step(t):
        t.store.put_problem(pid, language, "글", title=pid)
        t.store.add_submission(pid, "틀린 코드", False, language=language, status=status, detail=detail)
    return step


def labels_follow_language() -> None:
    """기본 문제의 태그와 되풀이한 실수 이름은 사용자가 고른 언어의 낱말이다(문제에 저장된 언어는 기본 문제가 모두 python이다)."""
    from tutor.knowledge.ontology import PATTERNS
    pid = ROWS[0]["id"]
    counting = next(key for key, (_, tech, _, _) in PATTERNS.items() if tech == "count_map")
    with patch.dict(server.BUILTIN[pid], {"ready": {"fact": {"patterns": [counting]}}, "languages": ["python", "java", "cpp", "javascript", "rust"]}):
        labels_checked(pid)


def labels_checked(pid: str) -> None:
    for language, word in (("java", "HashMap"), ("cpp", "map"), ("javascript", "Map"), ("python", "딕셔너리")):
        call("/api/language", id=pid, language=language)
        shown = next(row for row in call("/api/problems")[1]["problems"] if row["id"] == pid)
        assert shown["language"] == language and f"개수 세기({word})" in shown["tags"], (language, shown["tags"])  # 목록
        screen = call("/api/state", id=pid)[1]["problem"]
        assert f"개수 세기({word})" in screen["tags"], (language, screen["tags"])  # 문제 화면
    one, two = ROWS[0]["id"], ROWS[1]["id"]
    with server.tutor() as t:
        for pid_ in (one, two):
            t.store.put_problem(pid_, "python", "글", title=pid_)
            t.store.conn.execute("INSERT INTO pitfall_hit(problem_id, pitfall, code_hash, at) VALUES(?, 'pop_front', ?, 't')", (pid_, pid_))
        t.store.conn.commit()
    call("/api/language", id=one, language="python")
    assert [x["name"] for x in call("/api/report")[1]["pitfalls"]] == ["리스트 앞에서 꺼내기"]  # 마지막으로 고른 언어
    call("/api/language", id=one, language="java")
    assert [x["name"] for x in call("/api/report")[1]["pitfalls"]] == ["배열 앞에서 꺼내기"]
    call("/api/language", id=one, language="python")
    with server.tutor() as t:
        t.store.conn.execute("DELETE FROM pitfall_hit")
        t.store.conn.commit()


def pitfalls_repeated() -> None:
    """되풀이한 실수는 두 번 이상 나온 것만, 나온 문제와 함께 온다. 뜻이 겹치는 함정은 한 줄로 합친다."""
    one, two = ROWS[0]["id"], ROWS[1]["id"]
    assert call("/api/report")[1]["pitfalls"] == []
    with server.tutor() as t:
        for pid in (one, two):
            t.store.put_problem(pid, "python", "글", title=pid)
        for pid, pitfall, h in ((one, "off_by_one", "a"), (two, "wrong_compare", "b"), (one, "wrong_init", "c")):  # wrong_compare는 off_by_one과 한 줄
            t.store.conn.execute("INSERT INTO pitfall_hit(problem_id, pitfall, code_hash, at) VALUES(?, ?, ?, 't')", (pid, pitfall, h))
        t.store.conn.commit()
    rows = call("/api/report")[1]["pitfalls"]
    assert [(x["count"], sorted(p["id"] for p in x["problems"])) for x in rows] == [(2, sorted([one, two]))], rows  # wrong_init은 한 번이라 빠진다
    with server.tutor() as t:
        t.store.conn.execute("DELETE FROM pitfall_hit")
        t.store.conn.commit()


def readiness() -> None:
    """준비도(도움 없이 푼 기본 문제로만), 남은 것과 학습 지도, 주제를 가로지른 실패 꼴, 바뀐 강·약 규칙. 모델 0회."""
    import random
    import re
    levels = {(row["theme"], row["level"]): row["id"] for row in ROWS}
    ids = lambda keys, lv: [levels[(key, n)] for key in keys for n in lv]  # noqa: E731
    stage = lambda *steps: history(*steps)["readiness"]  # noqa: E731
    ess, freq = server.ESSENTIAL, server.FREQUENT
    # 선수 표: 키가 주제 목록과 같고, 먼저 익힐 주제가 늘 앞에 있다(순환이 없다). 군은 겹치지 않는다
    assert set(server.PREREQS) == set(ALGORITHMS) and all(server.MAP_ORDER[p] < server.MAP_ORDER[k] for k, ps in server.PREREQS.items() for p in ps)
    assert set(ess) | set(freq) <= set(ALGORITHMS) and not set(ess) & set(freq)
    # 이력 표: (이름, 기록, 기대 단계)
    hash5 = ids(["hash"], range(1, 6))
    table = [
        ("기록 없음", [], "hold"),
        ("도움 없이 4문제", [solve(pid) for pid in hash5[:4]], "hold"),
        ("해시만 5문제", [solve(pid) for pid in hash5], "building"),
        ("필수 하나가 한 문제 모자람", [solve(pid) for pid in ids(ess, (1, 2))[:-1]], "building"),
        ("필수 7개 딱 채움", [solve(pid) for pid in ids(ess, (1, 2))], "easy"),
        ("모두 해설을 먼저 봄", [solve(pid, helped=EARLY, solution_at=EARLY, solution_before_pass=True) for pid in ids(ess, (1, 2, 3))], "hold"),
        ("모두 튜터 기능을 먼저 씀", [solve(pid, helped=EARLY) for pid in ids(ess, (1, 2, 3))], "hold"),
        ("모두 튜터와 풂", [solve(pid, talk=EARLY) for pid in ids(ess, (1, 2, 3))], "hold"),
        ("통과 뒤에 튜터와 말함", [solve(pid, talk=LATE) for pid in ids(ess, (1, 2))], "easy"),
        ("통과 뒤에 힌트를 엶", [solve(pid, hints_seen=3, helped=LATE) for pid in ids(ess, (1, 2))], "easy"),
        ("통과 전에 힌트 하나", [solve(pid, hints_seen=1, helped=EARLY if pid == levels[("dfs", 2)] else LATE) for pid in ids(ess, (1, 2))], "building"),
        ("1·2단계만 26문제", [solve(pid) for pid in ids(ess + freq, (1, 2))], "easy"),
        ("3단계만 건너뜀", [solve(pid) for pid in ids(ess, (1, 2, 4, 5)) + ids(freq, (1, 2))], "practice"),
        ("실전 연습 단계 딱 채움", [solve(pid) for pid in ids(ess, (1, 2, 3)) + ids(freq, (1, 2))], "practice"),
        ("세부 없는 예전 기록", [solve(pid, detail=False) for pid in hash5], "building"),
        ("제출 3번째에 통과", [solve(pid, fails=2) for pid in hash5], "building"),
        ("한 문제는 제출 4번째에 통과", [solve(pid, fails=3 if n == 0 else 0) for n, pid in enumerate(hash5)], "hold"),
        ("한 문제에서 시간 초과 5번 뒤 통과", [solve(pid, fails=5 if n == 0 else 0) for n, pid in enumerate(hash5)], "hold"),
    ]
    for name, steps, want in table:
        got = stage(*steps)
        assert got["stage"] == want, (name, got)
        assert (got["remaining"] == []) == (want == "practice"), (name, got["remaining"])
    assert stage()["line"] == "아직 판단하기에 기록이 적어요. 도움 없이 5문제를 풀면 알려 드릴게요(지금 0문제)."
    short = stage(*[solve(pid) for pid in ids(ess, (1, 2))[:-1]])
    assert [(row["key"], row["level"], row["solved"], row["after"]) for row in short["remaining"]] == [("dfs", 2, 1, [server.theme_name("stack_queue")])]
    assert short["focus"]["key"] == "stack_queue" and short["focus"]["next"]["id"] == levels[("stack_queue", 1)]  # DFS의 선수 주제(스택·큐)부터
    easy = stage(*[solve(pid) for pid in ids(ess, (1, 2))])
    assert "쉬운 코딩테스트에 도전해 볼 만해요" in easy["line"] and "(14문제)" in easy["line"] and len(easy["remaining"]) == 13
    assert [row["key"] for row in easy["remaining"]] == sorted((row["key"] for row in easy["remaining"]), key=server.MAP_ORDER.get)  # 지도 순서
    # 남은 일은 행동으로: 푼 수가 모자라면 몇 문제 더, 단계가 모자라면 그 단계 하나 더(지금 도달한 단계와 함께)
    lefts = {row["key"]: row for row in easy["remaining"]}
    assert (lefts["hash"]["top"], lefts["hash"]["todo"]) == (2, "3단계 이상 문제 하나 더(지금 2단계까지)")
    assert (lefts["stack_queue"]["top"], lefts["stack_queue"]["todo"]) == (0, "도움 없이 2문제 더(2단계 이상 하나 포함)")
    assert short["remaining"][0]["todo"] == "도움 없이 1문제 더(2단계 이상 하나 포함)"
    assert next(row for row in stage(solve(levels[("hash", 3)]))["remaining"] if row["key"] == "hash")["todo"] == "도움 없이 1문제 더"  # 3단계 하나를 이미 풀었다
    # 먼저 익힐 주제를 못 익혔으면 그 주제부터: 스택·큐 없이 BFS·DFS만 남으면 스택·큐를 내세운다
    rest = stage(*[solve(pid) for pid in ids([k for k in ess if k not in ("bfs", "dfs")], (1, 2))])
    assert {row["key"] for row in rest["remaining"]} == {"bfs", "dfs"} and rest["focus"]["key"] == "stack_queue"
    assert next(row for row in rest["remaining"] if row["key"] == "bfs")["after"] == [server.theme_name("stack_queue")]
    # 추천 큐도 같은 선수 규칙: DFS만 푼 기록이면 이어서 풀기가 DFS 2단계가 아니라 선수 주제(스택·큐)의 첫 문제다. 준비도 칸의 다음 주제와 같다
    def stuck_ahead(body):  # 추천(쓰던 문제 말고)이 선수 주제가 모자란 주제의 문제인가: 준비도 칸의 '먼저 익힐 주제'와 견준다
        blocked = {row["name"] for row in body["readiness"]["remaining"] if row["after"]}
        return [row for row in body["next"] if row["why"] != "쓰던 문제예요." and row["theme_name"] in blocked]
    sole = history(solve(levels[("dfs", 1)]))
    assert not stuck_ahead(sole) and any(row["id"] == levels[("stack_queue", 1)] and row["why"].startswith("먼저 익힐 주제예요") for row in sole["next"])
    assert not any(row["id"] == levels[("dfs", 2)] for row in sole["next"])
    # 선수 주제를 익혔으면 그대로 이어서 풀기(바뀌지 않는다). 선수가 없는 주제(해시)와 기록이 아주 적은 때도 그대로
    ready = history(*[solve(pid) for pid in ids(["stack_queue", "brute_force"], (1, 2))], solve(levels[("dfs", 1)]))
    assert not stuck_ahead(ready)
    assert next(row for row in ready["next"] if row["why"] == "이어서 풀기" and row["theme_name"] == server.theme_name("dfs"))["id"] == levels[("dfs", 2)]
    assert any(row["id"] == levels[("hash", 2)] and row["why"] == "이어서 풀기" for row in history(solve(levels[("hash", 1)]))["next"])
    assert any(row["why"] == "새 주제 시작" for row in history()["next"])
    # 등록한 문제만 푼 기록은 준비도에 들지 않는다
    own = {f"own-{n}": SimpleNamespace(id=f"own-{n}", title="내 문제", sample=False, builtin=False, theme=ess[n % 2], theme_name="", level=0, mode="function") for n in range(6)}
    with patch.dict(server.PROBLEMS, own):
        assert stage(*[solve(pid) for pid in own])["stage"] == "hold"
        # 실패 꼴: 서로 다른 문제 3개·주제 2개 이상일 때만. 세부가 없는 예전 기록은 세지 않는다. 고친 수를 함께 말한다
        slow = {"accuracy": [4, 4], "efficiency": [0, 2]}
        three = list(own)[:3]
        assert history(*[fail(pid, "timeout", None) for pid in three])["patterns"] == []
        assert history(*[fail(pid, "timeout", slow) for pid in three[:2]])["patterns"] == []
        body = history(*[fail(pid, "timeout", slow) for pid in three], solve(three[0]))
        assert [(row["kind"], row["problems"], row["fixed"]) for row in body["patterns"]] == [("slow", 3, 1)], body["patterns"]
        assert body["patterns"][0]["line"].startswith("3문제(") and "그중 1문제는 고쳐서 통과했어요." in body["patterns"][0]["line"]
        same = {pid: SimpleNamespace(**{**vars(p), "theme": "hash"}) for pid, p in own.items()}
        with patch.dict(server.PROBLEMS, same):  # 한 주제에서만 나왔으면 말하지 않는다
            assert history(*[fail(pid, "timeout", slow) for pid in three])["patterns"] == []
        kinds = [("timeout", {"accuracy": [1, 4], "efficiency": [0, 2]}, "accuracy_timeout"), ("runtime_error", {"accuracy": [4, 4], "efficiency": [1, 2]}, "large_stop"),
                 ("output_limit", {"accuracy": [4, 4], "efficiency": [1, 2]}, "large_stop"),
                 ("runtime_error", {"accuracy": [3, 4], "efficiency": [0, 2]}, None), ("compile_error", {"accuracy": [0, 0], "efficiency": [0, 0]}, "compile:java")]
        for status, detail, want in kinds:
            got = history(*[fail(pid, status, detail, "java") for pid in three])["patterns"]
            assert [row["kind"] for row in got] == ([want] if want else []), (status, got)
        assert history(*[fail(pid, "entry_missing", {"accuracy": [0, 0]}, "java") for pid in three])["patterns"][0]["line"].startswith("Java 코드로 낸 3문제(")
    # 강·약 규칙: 튜터와 함께 첫 제출에 푼 3문제는 강점이 아니다. 한 문제에서 시간 초과 5번 뒤 통과는 약점이 아니다
    hashed = lambda body: next(row for row in body["themes"] if row["key"] == "hash")  # noqa: E731
    assert hashed(history(*[solve(pid, talk=EARLY) for pid in hash5[:3]]))["state"] == "weak"  # 강점이 아니고, 도움에만 기댄 통과라 약한 주제
    assert hashed(history(*[solve(pid) for pid in hash5[:3]]))["state"] == "strong"
    assert hashed(history(*[solve(pid, fails=5 if n == 0 else 0) for n, pid in enumerate(hash5)]))["state"] != "weak"
    # 다음 문제는 도움 없이 푼 단계가 기준이다: 모두 도움을 받아 1~4단계를 통과했으면 5단계가 아니라 가장 낮은 단계부터. 모두 도움 없이 풀었으면 5단계(그대로)
    nxt = lambda body: next(row for row in body["themes"] if row["key"] == "hash")["next"]["id"]  # noqa: E731
    assert nxt(history(*[solve(pid, helped=EARLY) for pid in hash5[:4]])) == hash5[0]
    assert nxt(history(*[solve(pid) for pid in hash5[:4]])) == hash5[4]
    assert nxt(history(solve(hash5[0]), solve(hash5[1]), solve(hash5[2], helped=EARLY))) == hash5[2]  # 도움 받은 3단계는 다시 풀 후보
    assert nxt(history(solve(hash5[0], helped=EARLY))) == hash5[0] and nxt(history(solve(hash5[0]))) == hash5[1]  # 기록이 아주 적을 때
    # 도움 받아 통과한 문제를 다시 권할 때는 사실대로 말한다(이어서 풀기가 아니다). 문제 목록의 '다음'도 보고서와 같다
    aided = history(*[solve(pid, helped=EARLY) for pid in hash5[:4]], listed=True)
    assert [row["why"] for row in aided["next"] if row["id"] == hash5[0]][0].startswith("도움 없이 다시 풀기(") and aided["listed"]["hash"]["id"] == hash5[0]
    assert all(row["why"] != "이어서 풀기" for row in aided["next"] if row["id"] in hash5)
    plain = history(*[solve(pid) for pid in hash5[:4]], listed=True)
    assert plain["listed"]["hash"]["id"] == hash5[4] == nxt(plain)
    # 도움에 기대 통과한 주제는 약한 주제다: 서로 다른 두 문제를 모두 도움을 받아 통과 → 약함, 도움 없이 푼 문제가 하나라도 있으면 아님, 한 문제만이면 판정하지 않는다
    assert hashed(history(*[solve(pid, helped=EARLY) for pid in hash5[:2]]))["state"] == "weak"
    assert hashed(history(*[solve(pid, hints_seen=1, helped=EARLY) for pid in hash5[:4]]))["state"] == "weak"
    assert hashed(history(solve(hash5[0]), solve(hash5[1], helped=EARLY)))["state"] == "progress"
    assert hashed(history(*[solve(pid) for pid in hash5[:2]]))["state"] == "progress"
    assert hashed(history(solve(hash5[0], helped=EARLY)))["state"] == "progress"
    weakened = history(*[solve(pid, helped=EARLY) for pid in hash5[:2]])
    assert any(row["key"] == "hash" and "도움 없이 푼 문제가 아직 없어요" in row["why"] for row in weakened["weaknesses"])
    # '새 주제 시작'은 학습 지도 순서이고, 선수 주제가 있는 주제는 선수 주제를 익힌 뒤에야 나온다(기록이 없으면 선수 없는 주제만)
    fresh = [row["theme_name"] for row in history()["next"] if row["why"] == "새 주제 시작"]
    assert fresh == [server.theme_name(key) for key in server.PREREQS if not server.PREREQS[key]][:len(fresh)], fresh
    # 주제를 '자동'으로 둔 등록 문제: 대조 검증이 all이면 풀이 계획의 유형으로 실패 수·약점 판정에 든다(기본 문제 칸·준비도에는 들지 않는다).
    # 고른 주제가 먼저이고, 계획의 유형과 다르면 둘을 나란히 보인다
    auto, auto2, partly, chosen = (server.register(GOOD)["id"] for _ in range(4))
    call("/api/problems/edit", id=chosen, **GOOD, theme="sort")
    for pid, verified in ((auto, "all"), (auto2, "all"), (partly, "examples")):
        server.cross_done(pid, {"verified": verified})

    def planned(t):
        for pid in (auto, auto2, partly, chosen):
            t.store.put_problem(pid, "python", GOOD["text"], title=GOOD["title"])
            t.adopt(pid, FIRST["ready"])  # 계획의 유형: 해시
            t.store.add_submission(pid, "느린 코드", False, status="timeout", detail={"accuracy": [3, 3], "efficiency": [0, 1]})
    body = history(planned)
    rows = {row["key"]: row for row in body["themes"]}
    assert (rows["hash"]["submissions"], rows["hash"]["fails"]["timeout"], rows["hash"]["solved"], rows["hash"]["state"]) == (2, 2, 0, "weak"), rows["hash"]
    assert rows["hash"]["why"].startswith("2문제에서 답은 맞았지만") and any(row["key"] == "hash" for row in body["weaknesses"])
    assert (rows["sort"]["submissions"], rows["hash"]["plan_differs"]) == (1, [])
    assert rows["sort"]["plan_differs"] == [{"id": chosen, "title": GOOD["title"], "planned": server.theme_name("hash")}]
    assert body["readiness"]["solved"] == 0 and body["readiness"]["stage"] == "hold"
    for pid in (auto, auto2, partly, chosen):
        call("/api/problems/delete", id=pid)
    # 도움을 받고 푼 뒤 '이 문제 처음부터'(대화가 지워진다): 다시 혼자 통과하기 전까지는 세지 않고, 그 '처음부터'에서 하루(REPEAT_GAP_HOURS)가
    # 지난 뒤에 혼자 다시 통과하면 센다. 하루 안의 통과(본 해설을 외워 붙일 수 있다)는 세지 않는다
    day = server.REPEAT_GAP_HOURS * 3600
    helped5 = [record(pid, ("talk", moment(0)), ("help", moment(1)), ("pass", moment(2)), ("reset", moment(3))) for pid in hash5]
    assert stage(*helped5)["solved"] == 0
    assert stage(*helped5, *[record(pid, ("fail", moment(4)), ("pass", moment(5))) for pid in hash5])["solved"] == 0
    assert stage(*helped5, *[record(pid, ("fail", moment(day)), ("pass", moment(day + 3))) for pid in hash5])["stage"] == "building"
    assert stage(*helped5, *[record(pid, ("help", moment(4)), ("pass", moment(day + 3))) for pid in hash5])["solved"] == 0  # 처음부터 뒤에도 도움을 받았다
    assert stage(*helped5, *[record(pid, *[("fail", moment(day + n)) for n in range(3)], ("pass", moment(day + 9))) for pid in hash5])["solved"] == 0  # 다시 푼 것도 제출 4번째
    # 통과와 같은 초의 '처음부터'는 그 통과를 새 풀이에 넣지 않는다. 도움 시각이 빈 옛 기록은 해설을 먼저 봤거나 본 힌트가 있으면 도움받은 것으로 본다
    assert stage(*[record(pid, ("help", moment(0)), ("pass", moment(day)), ("reset", moment(day))) for pid in hash5])["solved"] == 0
    assert stage(*[solve(pid, solution_before_pass=True) for pid in hash5])["solved"] == stage(*[solve(pid, hints_seen=1) for pid in hash5])["solved"] == 0
    # 혼자 푼 뒤의 도움·처음부터는 이미 센 것을 바꾸지 않는다
    assert stage(*[record(pid, ("pass", moment(0)), ("help", moment(1)), ("reset", moment(2)), ("help", moment(3))) for pid in hash5])["solved"] == 5
    # 언어를 바꾸는 것은 '처음부터'가 아니다(대화가 지워져도 학습 기록은 그대로)
    with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "report.db"):
        with server.tutor() as t:
            record(PID, ("help", moment(0)), ("pass", moment(1)))(t)
        call("/api/language", id=PID, language="javascript")
        call("/api/language", id=PID, language="python")
        with server.tutor() as t:
            assert t.store.study(PID)["reset_at"] is None and t.store.study(PID)["help_after_reset_at"] == t.store.study(PID)["help_first_at"] == moment(0)
        assert call("/api/report")[1]["readiness"]["solved"] == 0
    # 화면의 도움 길: 힌트 열기·해설 모드·튜터 대화는 쓴 시각을 남긴다. 통과 전이면 도움, 통과 뒤면 판정을 바꾸지 않는다
    for path, body in (("/api/hint", {}), ("/api/explain", {}), ("/api/turn", {"mode": "chair", "event": "start"})):
        for before in (True, False):
            def used(t, path=path, body=body, before=before):
                record(PID, ("fail", moment(0)), *([] if before else [("pass", moment(1))]))(t)
                with at(moment(2)), use_llm(FakeLlm({})):  # 해설 모드는 모델을 부른다(답이 없어 실패해도 쓴 것으로 센다). 바깥의 모델 0회 확인과 나눈다
                    call(path, id=PID, **body)
                record(PID, *([("pass", moment(3))] if before else []))(t)
            got = history(used)
            assert got["readiness"]["solved"] == (0 if before else 1), (path, before, got["readiness"])
    # 시각은 시간대가 달라도 견준다: 도움 09:00+09:00(= 00:00Z)은 통과 00:30Z보다 먼저다(글자 순서로는 뒤)
    tz = record(PID, ("help", moment(0)), ("pass", moment(1800, hours=0)))
    assert moment(0) > moment(1800, hours=0) and history(tz)["readiness"]["solved"] == 0
    # 남은 일: 그 주제에 아직 통과하지 않은 기본 문제로 채울 수 없으면 '처음부터'로 다시 풀라고 말한다
    spent = stage(*[record(pid, ("help", moment(0)), ("pass", moment(1))) for pid in hash5])
    assert next(row for row in spent["remaining"] if row["key"] == "hash")["todo"] == "이 주제의 남은 문제는 모두 이미 풀었어요. " + server.RESTART
    assert server.left("hash", 3, [1, 2], [], [])["todo"] == "3단계 이상 문제는 모두 이미 풀었어요. " + server.RESTART
    assert server.left("hash", 3, [1, 2], [4], [])["todo"] == "3단계 이상 문제 하나 더(지금 2단계까지)"
    # 불변식(시드 고정 무작위): 도움 없이 푼 문제를 더해도 단계가 내려가지 않는다, 남은 것이 비면 그때만 최고 단계, 내세운 주제의 선수 주제는 익혔다,
    # 문장의 숫자는 응답 값이다, 금지어가 없다
    order, rng = list(server.STAGES), random.Random(21)
    basic = lambda unaided, key: len(unaided.get(key, [])) >= server.MASTER_COUNT and max(unaided[key]) >= server.BASIC_LEVEL  # noqa: E731
    seen = set()
    for _ in range(500):
        dense = rng.random()  # 묶음마다 푼 정도를 달리해 네 단계가 모두 나오게 한다
        unaided = {key: [n for n in range(1, 6) if rng.random() < dense] for key in ALGORITHMS}
        started = {key for key in ALGORITHMS if rng.random() < 0.5}
        fresh = {key: [n for n in range(1, 6) if n not in unaided[key] and rng.random() < 0.5] for key in ALGORITHMS}  # 아직 통과하지 않은 문제
        got = server.readiness(unaided, started, fresh)
        seen.add(got["stage"])
        key, n = rng.choice(ALGORITHMS), rng.randint(1, 5)
        more = server.readiness({**unaided, key: sorted(set(unaided[key]) | {n})}, started, fresh)
        assert order.index(more["stage"]) >= order.index(got["stage"]), (unaided, key, n)
        assert (got["remaining"] == []) == (got["stage"] == "practice")
        assert got["focus"] is None or all(basic(unaided, p) for p in server.PREREQS[got["focus"]]), got
        assert got["solved"] == sum(map(len, unaided.values()))
        allowed = {got["solved"], len(got["remaining"]), server.READY_MIN, len(ess), len(freq), server.BASIC_LEVEL, server.REAL_LEVEL}
        assert {int(x) for x in re.findall(r"\d+", got["line"])} <= allowed and str(got["solved"]) in re.findall(r"\d+", got["line"]), got["line"]
        assert not any(word in text for word in BANNED for text in [got["line"], got["basis"], *got["rules"], *(row["todo"] for row in got["remaining"])])
        for row in got["remaining"]:  # 남은 일의 숫자도 응답 값이다
            assert row["top"] == max(unaided[row["key"]], default=0) and row["more"] == max(0, server.MASTER_COUNT - len(unaided[row["key"]]))
            assert {int(x) for x in re.findall(r"\d+", row["todo"])} <= {row["more"], row["level"], row["top"], server.REPEAT_GAP_HOURS}, row
            mine = unaided[row["key"]] + fresh[row["key"]]  # 아직 통과하지 않은 문제로 채울 수 있으면 그 일을, 없으면 '처음부터'를 말한다
            assert (server.RESTART in row["todo"]) == (len(mine) < server.MASTER_COUNT or max(mine, default=0) < row["level"]), (row, mine)
    assert seen == set(order), seen
    # 보고서 전체(무작위 이력 40묶음): 도움(힌트·해설·해설 모드·대화)·통과 뒤 도움·'처음부터'·제출 수를 섞은 기록에서
    # 단계가 '도움 없이 푼 문제'로만 정해지고, 강점 주제는 남은 것에 없다
    strongs = 0
    for _ in range(40):
        picked, unaided, steps = rng.sample(ROWS, rng.randint(0, len(ROWS))), {}, []
        for row in picked:
            kind, fails, clock = rng.choice(("", "", "", "late", "solution", "hint", "explain", "talk", "reset")), rng.choice((0, 0, 0, 1, 2, 3)), iter(range(100))
            tick = lambda: moment(next(clock))  # noqa: E731
            before = [("talk" if kind == "talk" else "help", tick())] if kind in ("solution", "hint", "explain", "talk", "reset") else []
            events = [*before, *[("fail", tick()) for _ in range(0 if kind == "reset" else fails)], ("pass", tick())]
            if kind == "late":
                events.append(("help", tick()))
            if kind == "reset":  # 도움을 받고 푼 뒤 처음부터 다시: 하루가 지나 fails번 틀리고 통과
                events += [("reset", tick()), *[("fail", moment(day + next(clock))) for _ in range(fails)], ("pass", moment(day + next(clock)))]
            if kind in ("", "late", "reset") and fails < server.UNAIDED_MAX_SUBMITS:
                unaided.setdefault(row["theme"], []).append(row["level"])
            steps.append(record(row["id"], *events))
        body = history(*steps)
        assert body["readiness"]["stage"] == server.readiness(unaided, set(), {})["stage"], unaided
        strong = {row["key"] for row in body["themes"] if row["state"] == "strong"}
        assert not strong & {row["key"] for row in body["readiness"]["remaining"]}, (strong, body["readiness"]["remaining"])
        assert not any(word in row["line"] for word in BANNED for row in body["patterns"])
        strongs += len(strong)
    assert strongs, "무작위 이력에 강점 주제가 한 번도 없으면 위 불변식이 비어 있다"


def screen_flows() -> None:
    """화면이 부르는 요청 그대로, 같은 초 안에서: 문제 열기 → 제출 → (통과하면) 다음 문제·해설 → '처음부터' → 다시 열기 → 보고서.
    통과하면 화면이 해설을 저절로 여는 것은 도움이 아니고, '처음부터' 뒤에는 해설·예전 힌트를 저절로 보여 주지 않으며,
    다시 풀어 되찾는 통과는 '처음부터'에서 하루(REPEAT_GAP_HOURS)가 지난 뒤의 것만 센다."""
    from contextlib import contextmanager
    from datetime import datetime, timedelta
    def later() -> str:  # 지금(방금 한 '처음부터')에서 하루가 조금 넘게 지난 때. 쓸 때마다 잰다(채점이 느린 기기에서 시험 앞부분이 1분을 넘겼다)
        return (datetime.now().astimezone() + timedelta(hours=server.REPEAT_GAP_HOURS, minutes=1)).isoformat(timespec="seconds")
    code = {row["id"]: row["solutions"]["python"] for row in ROWS}

    def opened(pid):  # app.js applyState: 본 힌트가 있으면 다시 보여 주고(peek), 이번 풀이에서 통과했으면 해설을 불러 둔다
        study = call("/api/state", id=pid, mode="chair", open=True)[1]["problem"]["study"]
        if study["hints_seen"]:
            call("/api/hint", id=pid, peek=True)
        if study["has_guide"] and study["passed_now"]:
            call("/api/solution", id=pid)
        return study

    sent = iter(range(1000))

    def submit(pid, source):  # 제출. 통과하면 화면이 결과 아래 '다음 문제'(보고서)와 해설을 부른다(같은 코드는 다시 남지 않으므로 낼 때마다 주석을 바꾼다)
        out = call("/api/submit", id=pid, code=f"{source}\n# {next(sent)}")[1]
        assert out.get("repeat") is False, out
        if out["ok"]:
            call("/api/report")
            call("/api/solution", id=pid)
        return out["ok"]

    def again(pid):  # '이 문제 처음부터' 뒤 화면이 상태를 다시 불러온다
        call("/api/reset", id=pid)
        return opened(pid)

    @contextmanager
    def fresh():
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "flow.db"):
            yield

    solved = lambda: call("/api/report")[1]["readiness"]["solved"]  # noqa: E731

    def judged(pid, source, want):  # 제출이 통과했고 도움 없이 푼 문제가 want개다. 아니면 무엇이 어긋났는지 보인다
        ok, got = submit(pid, source), solved()
        with server.tutor() as t:
            study = t.store.study(pid)
        assert ok and got == want, f"제출 통과 {ok}, 도움 없이 푼 문제 {got}(기대 {want}), 학습 기록 {study}, 지금 {datetime.now().astimezone().isoformat()}"
    levels = {(row["theme"], row["level"]): row["id"] for row in ROWS}
    with fresh():  # 정상 흐름: 필수 7개 주제의 1·2단계를 혼자 풀면(통과 뒤 해설이 저절로 열려도) 쉬운 코딩테스트 도전
        for pid in [levels[(key, n)] for key in server.ESSENTIAL for n in (1, 2)]:
            opened(pid)
            assert submit(pid, code[pid]), pid
        body = call("/api/report")[1]
        assert body["readiness"]["stage"] == "easy", body["readiness"]
        with server.tutor() as t:
            assert t.store.study(PID)["help_first_at"] is None  # 통과한 뒤 저절로 연 해설은 도움으로 적지 않았다
    with fresh():  # 통과 전 힌트 → 통과 → 처음부터: 예전 힌트·해설을 저절로 보여 주지 않고, 하루 뒤 혼자 통과하면 센다
        opened(PID)
        call("/api/hint", id=PID)
        judged(PID, CODE, 0)
        study = again(PID)
        assert (study["hints_seen"], study["passed_now"]) == (0, False), study
        with server.tutor() as t:
            assert t.store.study(PID)["help_after_reset_at"] is None
        judged(PID, CODE, 0)  # 같은 때 다시 낸 것(본 것을 그대로 붙일 수 있다)은 세지 않는다
        study = again(PID)
        with at(later()):
            judged(PID, CODE, 1)
    with fresh():  # 통과 전에 해설(정답 코드)을 보고 통과 → 처음부터 → 바로 다시 내면 세지 않고, 하루 뒤면 센다
        pid = levels[("sort", 1)]
        opened(pid)
        call("/api/solution", id=pid, force=True)
        judged(pid, code[pid], 0)
        again(pid)
        judged(pid, code[pid], 0)
        again(pid)
        with at(later()):
            judged(pid, code[pid], 1)
    with fresh():  # 처음부터 뒤에 힌트를 다시 열면 새 힌트를 연 것과 같이 도움이다
        opened(PID)
        call("/api/hint", id=PID)
        assert submit(PID, CODE)
        again(PID)
        assert call("/api/hint", id=PID)[1]["seen"] == 1
        with at(later()):
            judged(PID, CODE, 0)
    with fresh():  # '처음부터' 앞에 남긴 체크포인트를 되살리면 도움이다. '처음부터' 뒤에 남긴 것은 아니다
        opened(PID)
        call("/api/hint", id=PID)
        call("/api/checkpoint", id=PID, code=CODE, blocks={})
        assert submit(PID, CODE)
        again(PID)
        call("/api/checkpoint/restore", id=PID)
        with at(later()):
            judged(PID, CODE, 0)
    with fresh():
        opened(PID)
        call("/api/hint", id=PID)
        assert submit(PID, CODE)
        again(PID)
        soon = (datetime.now().astimezone() + timedelta(seconds=5)).isoformat(timespec="seconds")
        with patch.object(server, "now", lambda: soon):  # '처음부터'와 같은 초에 남긴 체크포인트는 앞의 것으로 본다(사람은 그 사이에 남기지 못한다)
            call("/api/checkpoint", id=PID, code="def solution(loans, k):\n    return []\n", blocks={})
        call("/api/checkpoint/restore", id=PID)
        with at(later()):
            judged(PID, CODE, 1)
    with fresh():  # 도움 없이 쓰던 코드의 체크포인트 → '처음부터' → 되살려 처음 통과: 첫 풀이에 도움이 없었으므로 센다
        opened(PID)
        call("/api/checkpoint", id=PID, code=CODE, blocks={})
        assert not submit(PID, "def solution(loans, k):\n    return []\n")
        again(PID)
        call("/api/checkpoint/restore", id=PID)
        with server.tutor() as t:
            assert t.store.study(PID)["help_first_at"] is None and t.store.study(PID)["help_after_reset_at"]
        judged(PID, CODE, 1)
    stuck = datetime.now()

    class Stopped(datetime):  # 시계가 멈춘 것처럼 늘 같은 순간을 준다(같은 초, 같은 밀리초)
        @classmethod
        def now(cls, tz=None):
            return stuck
    with fresh(), patch("tutor.store.sqlite.datetime", Stopped):  # 같은 순간의 실패 → '처음부터' → 통과 → (화면이 저절로 여는) 해설: 일어난 차례대로 판단한다
        opened(PID)
        assert not submit(PID, "def solution(loans, k):\n    return []\n")
        again(PID)
        judged(PID, CODE, 1)  # 첫 풀이에 도움이 없었다. 통과 뒤의 해설을 '처음부터' 뒤 통과 전의 도움으로 보지 않는다
        with server.tutor() as t:
            study, subs = t.store.study(PID), server.problem_subs(t, PID)
        assert study["help_first_at"] is None and subs[0]["at"] < study["reset_at"] < subs[1]["at"], (study, subs)
    with fresh():  # 언어를 바꿨다 돌아오는 것은 '처음부터'가 아니다: 도움을 받고 푼 문제는 하루 뒤에 다시 내도 세지 않는다
        opened(PID)
        call("/api/hint", id=PID)
        call("/api/hint", id=PID)
        assert submit(PID, CODE)
        call("/api/language", id=PID, language="javascript")
        study = call("/api/language", id=PID, language="python")[1]["problem"]["study"]
        assert (study["hints_seen"], study["passed_now"]) == (2, True), study  # 힌트 진행과 '이번 풀이에서 통과'가 그대로다(해설·신호가 저절로 열린다)
        with at(later()):
            judged(PID, CODE, 0)
        # '처음부터' 뒤: 이번 풀이의 힌트는 0부터, 보고서의 본 힌트 수는 누적(2), 다른 언어로 쓰던 코드는 비운다
        call("/api/language", id=PID, language="javascript")
        call("/api/code", id=PID, code=JS, language="javascript")
        call("/api/language", id=PID, language="python")
        again(PID)
        assert call("/api/language", id=PID, language="javascript")[1]["problem"]["code"] == ""
        study = call("/api/language", id=PID, language="python")[1]["problem"]["study"]
        assert (study["hints_seen"], call("/api/hint", id=PID, peek=True)[1]["shown"]) == (0, []), study
        assert next(row for row in call("/api/report")[1]["themes"] if row["key"] == "hash")["hints"] == 2
    with fresh():  # '처음부터'는 해설 모드의 글을 지운다(다른 언어로 보관한 것도). 남아 있으면 기록 없이 다시 보인다
        opened(PID)
        with server.tutor() as t:
            t.store.conn.execute("UPDATE tutor_session SET explain_json=? WHERE problem_id=?", (json.dumps({"sections": [{"title": "흐름", "body": "개수를 센다"}]}), PID))
            t.store.conn.commit()
        assert call("/api/state", id=PID)[1]["session"]["explain"]
        call("/api/language", id=PID, language="javascript")  # 파이썬의 해설 모드 글을 보관한다
        call("/api/language", id=PID, language="python")
        assert call("/api/state", id=PID)[1]["session"]["explain"]
        call("/api/language", id=PID, language="javascript")  # 파이썬의 글은 보관된 채로 다른 언어에서 '처음부터'
        again(PID)
        assert not call("/api/language", id=PID, language="python")[1]["session"]["explain"]
        with server.tutor() as t:
            t.store.conn.execute("UPDATE tutor_session SET explain_json=? WHERE problem_id=?", (json.dumps({"sections": [{"title": "흐름", "body": "개수를 센다"}]}), PID))
            t.store.conn.commit()
        again(PID)  # 지금 언어의 글
        assert not call("/api/state", id=PID)[1]["session"]["explain"]
    with fresh():  # 처음부터 뒤에 사용자가 해설을 직접 열면 도움이다(통과한 적이 있어 잠겨 있지 않다)
        opened(PID)
        call("/api/hint", id=PID)
        assert submit(PID, CODE)
        again(PID)
        call("/api/solution", id=PID)
        with at(later()):
            judged(PID, CODE, 0)


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
    pid, pid2 = (server.register({**GOOD, "theme": key})["id"] for _ in range(2))
    plain = server.register(GOOD)["id"]  # 주제 없는 문제
    listed = {row["id"]: row for row in call("/api/problems")[1]["problems"]}
    assert (listed[pid]["theme_name"], listed[plain]["theme_name"], call("/api/state", id=pid)[1]["problem"]["theme"]) == (server.theme_name(key), "", key)
    with server.tutor() as t:
        for one in (pid, pid2):
            t.store.add_submission(one, "느린 코드", False, status="timeout", detail={"accuracy": [3, 3], "efficiency": [0, 1]})
        for n in range(3):
            t.store.add_submission(plain, f"틀린 코드 {n}", False, status="timeout")
        t.adopt(plain, FIRST["ready"])  # 튜터가 짠 계획의 알고리즘(hash)은 주제를 정하지 않은 문제에 보여 주기만 한다
    body = call("/api/report")[1]
    row = next(row for row in body["themes"] if row["key"] == key)
    assert (row["state"], row["submissions"], row["fails"]["timeout"], row["solved"], row["total"]) == ("weak", 2, 2, 0, before[key]["total"])
    assert row["why"].startswith("2문제에서 답은 맞았지만") and any(weak["key"] == key for weak in body["weaknesses"])
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


def passed_reopen() -> None:
    """통과한 풀이를 다시 열면(화면 코드 확인): 풀던 중의 실패 말, '끝까지 쓰는 중' 안내, 틀린 곳 찾기의 옛 질문이 지금 상태처럼 남지 않는다. 브라우저 동작은 화면 확인으로 본다."""
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    assert "const passedNow = () => !!(S.problem && S.problem.study.passed_now);" in js
    assert "ownWayOn() && !passedNow() ?" in js  # 통과한 뒤에는 '끝까지 내 방식으로 쓰는 중' 안내를 걷는다
    assert "const result = !passedNow() && st && st !== \"pass\"" in js  # 블록 아래의 옛 실패 한 줄도
    assert "if (passedNow()) html += '<p class=\"notice\" role=\"status\">이번 풀이는 통과했어요." in js  # 튜터 대화의 맨 아래가 옛 실패 말이어도 통과를 알린다
    assert 'if (d.passed && html) html = `<details class="old-talk">' in js and ".old-talk summary" in css  # 통과한 뒤 틀린 곳 찾기의 옛 대화는 접는다
    assert "S.debug.passed = true; S.debug.line = null;" in js  # 제출로 통과해도 옛 질문과 짚은 줄을 걷는다
    assert call("/api/state", id=PID)[1]["problem"]["study"].get("passed_now") is not None  # 화면이 쓰는 값


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


def state_names_by_mode() -> None:
    """상태는 요청의 방식으로 블록 이름을 가린다: 가이드는 지금 블록 이름이 보이고, 의자는 아직 찾지 못한 지금 블록 이름이 가려진다.
    화면은 문제를 열 때 그 문제에 기억한 방식을 보내야 한다(직전 방식이 아니라) — 아니면 가이드가 이름을 가린 채 열린다."""
    call("/api/reset", id=PID)
    call("/api/turn", id=PID, mode="guide", event="start")
    guide, chair = (call("/api/state", id=PID, mode=m)[1]["session"] for m in ("guide", "chair"))
    assert guide["open_count"] == chair["open_count"] == 1
    assert [b["name"] for b in guide["blocks"]] == ["개수 세기", None], guide["blocks"]
    assert [b["name"] for b in chair["blocks"]] == [None, None], chair["blocks"]
    call("/api/reset", id=PID)


def keyboard_focus() -> None:
    """키보드 초점(화면 코드 확인): 키보드로 누른 단추가 사라지면 초점을 이어 갈 자리로 돌려 놓고, 건너뛰기 링크는 주소를 바꾸지 않고 본문 제목으로 옮기며,
    코드 칸에 초점이 있는 동안 Esc 다음 Tab 안내가 보인다. 사용법 창은 처음부터 showModal로 연다. 브라우저 동작은 화면 확인으로 본다."""
    js, css, html = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8")
    assert "function focusAfter(el)" in js and 'e.detail === 0 && e.target.closest("#view-code button")' in js and "}, true);" in js  # 다시 그리기 전에(잡기 단계에서) 받는다
    assert '"#say"' in js[js.index("function focusAfter(el)"):js.index("document.addEventListener(\"focusin\"")] and 'textarea[data-block=' in js  # 첫 질문 → 입력 칸, 블록 확인 → 그 블록 칸
    assert 'e.target.closest("a.skip")' in js and "e.preventDefault();" in js[js.index('a.skip'):js.index("codeCell")] and '<main id="main" tabindex="-1">' in html  # 주소를 바꾸면 화면이 홈으로 갔다
    assert 'id="tab-hint"' in html and "Esc를 누른 뒤 Tab" in html and ".tab-hint.on { visibility: visible; }" in css and '$("tab-hint").classList.toggle("on", codeCell(e.target))' in js
    assert "tour.showModal" in js  # 사용법 창은 모달: Tab이 창 안에서 돈다


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


def guide_spoken() -> None:
    """튜터와 차례로: 말로 빈칸을 맞혀도 다음 블록이 열리지 않는다(코드 칸이 빈 채 지나가 완료처럼 보였다). 블록 코드 확인이 통과해야 연다."""
    from tutor.turn.moves import WRITE_TIP
    pid = server.register({"title": FIRST["title"], "text": FIRST["text"], "cases": [{"input": e["input"], "expected": e["expected"]} for e in FIRST["examples"]]})["id"]
    with server.tutor() as t:
        t.adopt(pid, FIRST["ready"])
    call("/api/turn", id=pid, mode="guide", event="start")
    with use_llm(FakeLlm({"guide.judge": ["[check]Y g"]})):
        body = call("/api/turn", id=pid, mode="guide", event="message", text="이름마다 몇 번 나왔는지 세요")[1]
    assert body["open_count"] == 1 and body["messages"][-1]["text"] == WRITE_TIP and body["messages"][-1]["block_index"] == 0, body
    body = call("/api/turn", id=pid, mode="guide", event="block_filled", block_id="b1", code="\n".join(LINES[:5]))[1]
    assert body["open_count"] == 2, body


def same_check_once() -> None:
    """바뀌지 않은 블록 코드를 거듭 확인해 같은 말이 나오면 대화에 또 쌓지 않는다(모델 0회). 실제 기본 문제·채점기로, 이름을 짝짓지 못해 '확인 전'으로 끝나는 확인.
    코드를 바꾸면 다시 쌓인다. 화면은 쌓지 않은 까닭을 블록 칸에 알린다."""
    from tutor.turn.code_check import hold_name
    pid = "hash_2_steady_climbers"
    call("/api/turn", id=pid, mode="guide", event="start")
    first = call("/api/turn", id=pid, mode="guide", event="block_filled", block_id="b1", code="records = {}")[1]
    assert first["unsure"] and not first["repeated"] and first["messages"][-1]["text"] == hold_name(["last", "visits", "broken"]), first["messages"][-1]
    for _ in range(2):
        again = call("/api/turn", id=pid, mode="guide", event="block_filled", block_id="b1", code="records = {}")[1]
        assert again["unsure"] and again["repeated"] and again["messages"] == first["messages"], again["messages"][len(first["messages"]):]
    changed = call("/api/turn", id=pid, mode="guide", event="block_filled", block_id="b1", code="records = {}\nseen = {}")[1]
    assert not changed["repeated"] and len(changed["messages"]) == len(first["messages"]) + 2, changed
    js = (HERE / "app.js").read_text(encoding="utf-8")
    assert "r.data.repeated) S.note.blocks = { type: \"warn\", text: REPEATED }" in js


def result_guides() -> None:
    """채점 결과와 방식 화면의 안내(화면 코드 확인): 큰 입력의 실행 오류는 시간 부족이라 하지 않고, 효율성만 실패하면 ‘틀린 곳 같이 찾기’가 없는 까닭을 말하며,
    튜터 방식 전환 단추는 무엇이 바뀌는지 말하고, 튜터의 질문으로에서 코드 칸으로 가는 길이 보인다. 브라우저 동작은 화면 확인으로 본다."""
    js = (HERE / "app.js").read_text(encoding="utf-8")
    assert 'c.kind === "efficiency" && (c.status === "timeout" || c.status === "skipped")' in js and "const slowOnly = slowOnlyOf(r);" in js  # 시간 초과만 '느려요'
    assert "아주 큰 입력에서 실행 중 오류가 났어요: " in js and "아주 큰 입력에서 답이 달라요" in js and "답이 맞아서 ‘틀린 곳 같이 찾기’는 열지 않아요." in js
    assert "혼자 풀기로 바뀌어요" not in js and "오른쪽 칸이 해설로 바뀌어요" in js and "오른쪽 칸이 힌트로 바뀌어요" in js
    assert 'S.talk === "chair" && !s.blocks.some((b, i) => blockState(b, i) === "found")' in js and 'data-tab="direct">코드 전체 칸 열기' in js
    assert '"message": SLOW_MESSAGE' in (HERE / "server.py").read_text(encoding="utf-8")


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


def hint_by_block() -> None:
    """혼자 풀기의 힌트는 블록마다 고른다(모델 0회): 막힌 블록부터 열고, 본 힌트 수(도움)는 하나씩 는다. '처음부터'와 예전 기록도 맞게 읽는다."""
    pid = server.register({"title": FIRST["title"], "text": FIRST["text"], "cases": [{"input": e["input"], "expected": e["expected"]} for e in FIRST["examples"]]})["id"]
    with server.tutor() as t:
        t.adopt(pid, FIRST["ready"])
    seen = lambda: call("/api/state", id=pid)[1]["problem"]["study"]["hints_seen"]  # noqa: E731
    picked = call("/api/hint", id=pid, block=2)[1]
    assert (picked["block"], picked["step"], picked["seen"], [b["seen"] for b in picked["blocks"]], seen()) == (2, 1, 1, [0, 1], 1), picked
    assert [(h["block"], h["step"]) for h in call("/api/hint", id=pid, peek=True)[1]["shown"]] == [(2, 1)]
    for bad in (0, 3, "2", True):
        assert "블록을 다시 골라" in refuses("/api/hint", id=pid, block=bad), bad
    last = [call("/api/hint", id=pid, block=2)[1] for _ in range(3)][-1]  # 그 블록을 다 본 뒤에는 그 블록의 마지막 힌트를 다시 준다(세지 않는다)
    assert (last["step"], last["name"], last["seen"], seen()) == (3, "k번째에 꽂기", 3, 3), last
    assert [b.get("name") for b in last["blocks"]] == [None, "k번째에 꽂기"]  # 다 본 블록만 이름이 보인다
    first = call("/api/hint", id=pid)[1]  # 블록을 고르지 않으면 아직 다 보지 않은 첫 블록
    assert (first["block"], first["step"], first["seen"]) == (1, 1, 4), first
    rows = server.read_json(server.HINTS_FILE, {})
    server.write_json(server.HINTS_FILE, {**rows, pid: {"from": 99, "seen": {"2": 3, "1": 1}}})  # 이번 풀이의 것이 아닌 기록: 본 수를 블록 1부터 나눈다
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [3, 1]
    server.write_json(server.HINTS_FILE, rows)
    call("/api/reset", id=pid)  # '처음부터' 뒤에는 블록마다 본 수도 처음부터(누적 수는 남는다)
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [0, 0] and seen() == 0
    assert (call("/api/hint", id=pid, block=2)[1]["step"], seen()) == (1, 1)
    with server.tutor() as t:
        assert t.store.study(pid)["hints_seen"] == 5 and t.store.study(pid)["help_first_at"]


def compile_hints() -> None:
    """컴파일 오류에는 실행 오류처럼 쉬운 설명 한 줄이 붙는다(흔한 것만: 없는 이름·멤버·클래스, 형이 맞지 않음). 흔하지 않은 오류는 원문만(되돌리면 실패)."""
    java = "Solution.java:5: error: cannot find symbol\n    count.add(1);\n         ^\n  symbol:   method add(int)\n  location: variable count of type int\n1 error"
    assert "`add`라는 이름을 찾지 못했어요" in server.compile_hint(java, "java"), server.compile_hint(java, "java")
    assert "`foo`라는 이름을 찾지 못했어요" in server.compile_hint("Solution.java:3: error: cannot find symbol\n  symbol:   variable foo\n1 error", "java")
    assert "값의 형이 맞지 않아요" in server.compile_hint("Solution.java:4: error: incompatible types: String cannot be converted to int\n1 error", "java")
    assert "값의 형이 맞지 않아요" in server.compile_hint("error[E0308]: mismatched types\n --> main.rs:3:5", "rust")
    assert "문법에 맞지 않는" in server.compile_hint("  File \"solution.py\", line 2\nSyntaxError: invalid syntax", "python")
    assert server.compile_hint("Solution.java:2: error: ';' expected\n1 error", "java") == ""
    # 실제 컴파일러가 낸 글(rustc·javac·g++): Rust의 백틱 이름도 쉬운 말이 붙는다
    for text, language, name in (("error[E0425]: cannot find value `x` in this scope\n --> a.rs:1:42\n  |\n1 | fn main(){ println!(\"{}\", x); }\n", "rust", "x"),
                                 ("error[E0599]: no method named `lenght` found for struct `Vec<{integer}>` in the current scope\n --> b.rs:1:44\n", "rust", "lenght"),
                                 ("error[E0425]: cannot find type `HashMap` in this scope\n --> c.rs:1:19\n", "rust", "HashMap"),
                                 ("Solution.java:1: error: cannot find symbol\npublic class Solution { int f(){ return foo; } }\n                                        ^\n  symbol:   variable foo\n  location: class Solution\n1 error\n", "java", "foo"),
                                 ("m.cpp:1:21: error: use of undeclared identifier 'bar'\n    1 | int main(){ int a = bar; return a; }\n      |                     ^~~\n", "cpp", "bar")):
        assert f"`{name}`" in server.compile_hint(text, language) and "찾지 못했어요" in server.compile_hint(text, language), (language, name)
    body = server.result_body({"status": "compile_error", "reason": "", "compile": java, "cases": [], "language": "java"})
    assert "`add`라는" in body["compile_hint"] and server.result_body({**{"status": "failed", "reason": "", "compile": "", "cases": [], "language": "java"}})["compile_hint"] == ""


def language_switch_state() -> None:
    """언어를 바꾸면 언어마다 계획이 다른 문제(직접 넣은 문제)의 본 힌트는 새 계획에서 0이고, 피드백은 본 제출의 언어를 싣는다(되돌리면 실패)."""
    pid = server.register({"title": FIRST["title"], "text": FIRST["text"], "cases": [{"input": e["input"], "expected": e["expected"]} for e in FIRST["examples"]]})["id"]
    with server.tutor() as t:
        t.adopt(pid, FIRST["ready"])
    call("/api/hint", id=pid, block=1)
    call("/api/hint", id=pid, block=1)
    call("/api/language", id=pid, language="javascript")
    with server.tutor() as t:
        t.adopt(pid, FIRST["ready"])  # 튜터가 새 언어의 계획을 만든 것으로 본다
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [0, 0]
    assert call("/api/hint", id=pid)[1]["seen"] == 1  # 새 계획의 첫 힌트부터
    assert call("/api/hint", id=pid)[1]["seen"] == 2  # 새 언어에서 둘 이상 봐도 쌓인 수로 다시 나누지 않는다
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [2, 0]
    assert call("/api/hint", id=pid)[1]["step"] == 3  # 다음 힌트도 같은 블록의 다음 것
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [3, 0]
    assert call("/api/state", id=pid)[1]["problem"]["study"]["hints_seen"] == 3  # 화면의 수도 블록별 표시와 같다
    call("/api/language", id=pid, language="python")  # 원래 언어로 돌아와도 어긋나지 않는다
    assert [b["seen"] for b in call("/api/hint", id=pid, peek=True)[1]["blocks"]] == [0, 0]
    assert call("/api/state", id=pid)[1]["problem"]["study"]["hints_seen"] == 0
    call("/api/language", id=pid, language="javascript")
    with server.tutor() as t:
        sub = t.store.add_submission(pid, "x", False, language="python")
        t.store.conn.execute("INSERT INTO feedback(problem_id, submission_id, body_json) VALUES(?, ?, ?)", (pid, sub, json.dumps({"submission_id": sub, "analysis": "a"})))
        t.store.conn.commit()
    assert call("/api/feedback/get", id=pid)[1]["language"] == "python" and call("/api/state", id=pid)[1]["problem"]["language"] == "javascript"


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
    big = {**fake, "cases": [{**case, "id": "1", "kind": "example", "status": "passed"}, {**case, "id": "2", "kind": "efficiency", "status": "timeout"},
                             {**case, "id": "3", "kind": "efficiency", "status": "failed", "expected": "9" * 300, "got": "8" * 300}]}
    long = server.tutor_view(big)["cases"][2]  # 큰 입력의 값은 줄여 싣고, 함정을 견줄 꼴은 줄이기 전의 값으로
    assert (long["input"], len(long["expected"]), len(long["got"]), long["out"]) == ("(아주 큰 입력)", server.BIG_SHOWN + len("…(앞부분만)"), server.BIG_SHOWN + len("…(앞부분만)"), server.out_key("8" * 300)), long
    assert not server.slow_only(big) and server.slow_only({**big, "cases": big["cases"][:2] + [{**case, "id": "3", "kind": "efficiency", "status": "skipped"}]})  # 큰 입력에서 틀린 답은 시간 문제가 아니다
    assert not server.slow_only({**big, "cases": big["cases"][:2] + [{**case, "id": "3", "kind": "efficiency", "status": "runtime_error"}]})
    sent, server.grade = [], lambda *args, **kwargs: big
    try:  # 작은 입력이 다 맞으면 큰 입력의 틀린 답으로 틀린 곳을 찾는다. 같이 난 시간 초과는 빼서 시간 이야기로 새지 않는다
        with patch.object(server.Tutor, "debug", lambda self, pid, code, report, text=None: sent.append(report) or SimpleNamespace(status=200, body={"messages": []})):
            call("/api/debug", id=pid, code="class Big {}")
    finally:
        server.grade = grade
    assert sent[0]["status"] == "failed" and [c["id"] for c in sent[0]["cases"]] == ["1", "3"], sent
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


def retired_languages() -> None:
    """지원을 접은 언어(go·kotlin)로 저장된 자료: 문제를 열면 오류 없이 파이썬으로 열리고(그 언어의 코드는 지우지 않고 보관), 등록 문제의 언어·풀이·시작 코드 목록에서는 빠진다."""
    own = server.register(GOOD)["id"]  # 등록 문제를 go로 저장해 둔 채(문제를 열기 전에) 목록·보고서부터 부른다
    with server.tutor() as t:
        t.store.put_problem(own, "go", server.PROBLEMS[own].text, direct_code="func solution() {}", title="t")
        t.store.set_language(PID, "go")
        t.store.update_code(PID, "func solution() {}")
    assert server.starter_of(server.PROBLEMS[own], "go") == ""  # 지원 밖의 언어는 예외 없이 빈 시작 코드
    server.retire_languages()  # 서버를 켤 때 한 번
    with server.tutor() as t:
        assert t.store.load(own).language == "python" and t.store.load(PID).language == "python"
    assert server.read_json(server.CODES_FILE, {})[own]["go"] == "func solution() {}"
    assert call("/api/problems")[1]["problems"] and call("/api/report")[1]["summary"]
    server.LANG.pop(PID, None)
    state = call("/api/state", id=PID)[1]["problem"]
    assert state["language"] == "python" and "go" not in state["languages"] and "kotlin" not in state["languages"], state
    assert server.read_json(server.CODES_FILE, {})[PID]["go"] == "func solution() {}"
    assert next(row for row in call("/api/problems")[1]["problems"] if row["id"] == PID)["language"] == "python"
    row = server.supported({"languages": ["python", "go", "kotlin", "rust"], "solutions": {"python": "a", "go": "b", "kotlin": "c"},
                            "starters": {"go": "b", "rust": "d"}, "limits": {"kotlin": 1.0, "python": 1.0}})
    assert row == {"languages": ["python", "rust"], "solutions": {"python": "a"}, "starters": {"rust": "d"}, "limits": {"python": 1.0}}, row


def tools() -> None:
    """이 기기의 언어 도구: 다섯 언어 모두 있음·없음이 오고, 서버를 돌리는 Python은 있다. 문제 상태에도 같은 모양으로 실린다."""
    got = call("/api/tools")[1]["tools"]
    assert set(got) == set(server.check_judge().LANGUAGES) and len(got) == 5 and got["python"] is True
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
    bar = "days | limit | result\n[2, 3] | 6 | 5\n[4, 5] | 1 | 4\n\n설명"  # 구분선 없이 |로만 나눈 표: 줄마다 칸 수가 같을 때만
    assert found(text=bar)["cases"] == [{"input": "[[2, 3], 6]", "expected": "5"}, {"input": "[[4, 5], 1]", "expected": "4"}] and found(text=bar)["names"] == ["days", "limit"]
    assert len(found(text="days | limit | result\n[2, 3] | 6 | 5\n[4, 5] | 1 | 4 | 9\n[7] | 2 | 3")["cases"]) == 1  # 칸 수가 다른 줄에서 끝난다
    for text in ("a | b | result\nx | y | z", "비트 연산: a | b 는 둘 중 하나라도 1이면 1입니다.\nresult = a | b", "x | y | result\na | b | c\n1 | 2 | 3"):  # 비트 연산이나 설명 글의 |
        assert found(text=text)["cases"] == [], text
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


def detect_merge() -> None:
    """감지의 나머지 길: 아주 긴 글은 모델에 보내지 않는다. touched에 mode가 있으면 보낸 방식으로 읽는다. 고친 칸 모양이 틀리면 거절.
    문제 글로 보이지 않는다는 감지 결과(problem: false)를 실어 등록하면 열어도 뒤 준비를 하지 않고, /api/problems/prepare를 보내야 준비한다."""
    import time
    from tutor.main import Outcome

    boj = "합\n\n두 정수의 합을 출력한다.\n1 ≤ a, b ≤ 10\n\n예제 입력 1\n1 2\n\n예제 출력 1\n3\n"
    fake = FakeLlm({"ingest.outline": [{"problem": False, "mode": "function"}]})
    with use_llm(fake), patch.object(server, "connected", lambda: True):
        long = "1 ≤ n ≤ 5\n" * 5000
        assert call("/api/problems/detect", text=long)[1] == call("/api/problems/detect", text=long, fast=True)[1] and not fake.calls
    assert call("/api/problems/detect", text=boj, fast=True)[1]["mode"] == "program"
    forced = call("/api/problems/detect", text=boj, fast=True, mode="function", touched=["mode"])[1]
    assert (forced["mode"], forced["cases"]) == ("function", []), forced
    assert "글이어야" in refuses("/api/problems/detect", text=None) and "모양" in refuses("/api/problems/detect", text="x", touched=[{"a": 1}])
    said = "합 구하기\n문제 설명\n예를 들어 numbers가 [1, 2]이면 3을 반환한다.\n제한사항\n1 ≤ n ≤ 10"  # 모델이 글에 없는 인자 이름을 지어냈다
    made = {"problem": True, "title": 1, "mode": "function", "names": ["made_up_arg"], "cases": [{"line": 3, "args": ["[1, 2]"], "expected": "3"}]}
    for touched, bad in (([], "made_up_arg"), (["cases"], "made_up_arg"), ([], "<img src=x onerror=alert(1)>"), ([], "__import__('os')")):
        fake = FakeLlm({"ingest.outline": [{**made, "names": [bad]}]})
        with use_llm(fake), patch.object(server, "connected", lambda: True):
            got = call("/api/problems/detect", text=said, touched=touched)[1]
        assert got["names"] == [] and bad not in json.dumps(got, ensure_ascii=False), got
        assert (got["suggest"]["cases"] if touched else got["cases"]) == [{"input": "[[1, 2]]", "expected": "3"}], got
    fake = FakeLlm({"ingest.outline": [{**made, "names": ["numbers"]}]})
    with use_llm(fake), patch.object(server, "connected", lambda: True):
        assert call("/api/problems/detect", text=said, touched=["cases"])[1]["suggest"]["names"] == ["numbers"]  # 글에 있는 이름은 예시와 함께 제안한다
    assert server.RANGE.search("1 \\le n") and server.RANGE.search("1 \\leq n") and not server.RANGE.search("1 \\left( x \\right)") and not server.RANGE.search("x \\gets 1")

    tries = []
    with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", lambda self, problem_id: tries.append(problem_id) or Outcome(200, {"blocks": 0, "patterns": []})):
        pid = server.register({**GOOD, "problem": False})["id"]
        assert call("/api/state", id=pid, open=True)[1]["problem"]["hold"] and tries == [] and pid not in server.PREPARED, tries  # 열어도 준비하지 않는다
        call("/api/problems/prepare", id=pid)
        for _ in range(200):
            if pid not in server.PREPARING:
                break
            time.sleep(0.02)
        assert tries == [pid] and not call("/api/state", id=pid)[1]["problem"]["hold"], tries
        assert "고치거나" in refuses("/api/problems/prepare", id=PID)  # 기본 문제는 미룬 것이 없다


INGEST = HERE / "testdata" / "ingest"  # 문제 넣기 시험 자료: 지어 쓴 문제 글과 기대(raw는 줄 목록)
DETECT_KEYS = {"problem", "notice", "title", "mode", "names", "cases", "skipped", "kinds", "bounds", "many", "suggest"}  # 감지 응답에 늘 있는 칸
DETECT_MORE = {"missed", "spill"}  # 기존 읽기 함수(table_cases·sample_cases)가 알릴 때만 있는 칸
LINE_KINDS = {"title", "body", "limits", "input", "output", "sample", "noise", ""}  # kinds: 줄마다 하나
NOT_PROBLEM = "문제 글로 보이지 않아요"
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))
NOISE_TOP = ["홈   문제   문제집   대회   게시판", "문제 목록 > 연습 > 이 문제"]
NOISE_MID = ["지금 가입하면 첫 달 무료 · 광고", ""]
NOISE_END = ["", "", "출처: 연습 문제 묶음", "알고리즘 분류", "구현", "", "댓글 2", "방문자1: n이 10만 이하라서 그냥 돌려도 되네요.", "방문자2: 예제 설명이 친절해요."]


def corpus() -> list[dict]:
    return [{**row, "raw": "\n".join(row["raw"])} for row in (json.loads(path.read_text(encoding="utf-8")) for path in sorted(INGEST.glob("*.json")))]


def squash(text) -> str:
    """견주기용: 전각을 반각으로(NFKC), 폭 없는 글자를 빼고, 빈칸(NBSP·전각 공백·탭 포함)을 하나로."""
    return " ".join(unicodedata.normalize("NFKC", str(text)).translate(ZERO_WIDTH).split())


def trimmed(cases: list[dict]) -> list[dict]:
    """케이스의 입력·기대. 채점기처럼 줄 끝 공백은 보지 않는다."""
    return [{key: "\n".join(line.rstrip() for line in str(case[key]).split("\n")) for key in ("input", "expected")} for case in cases]


def detect(text: str, **body) -> dict:
    out = call("/api/problems/detect", text=text, **body)[1]
    assert DETECT_KEYS <= set(out) <= DETECT_KEYS | DETECT_MORE, sorted(out)
    assert len(out["kinds"]) == len(text.splitlines()) and set(out["kinds"]) <= LINE_KINDS, out["kinds"]
    return out


def line_at(text: str, piece: str, whole: bool = False) -> int:
    """piece가 든(whole이면 그 줄 전체인) 첫 줄의 번호. 1부터 센다(구획 나누기에 주는 줄 번호와 같다)."""
    want = squash(piece)
    return next(n for n, line in enumerate(text.splitlines(), 1) if (squash(line) == want if whole else want in squash(line)))


def summary(out: dict, title: bool = True) -> dict:
    """변형 불변으로 견줄 것: 문제인가·방식·인자 이름·케이스·범위·답이 여럿(·제목)."""
    return {"problem": out["problem"], "mode": out["mode"], "names": out["names"], "cases": trimmed(out["cases"]),
            "bounds": sorted(squash(line) for line in out["bounds"]), "many": out["many"], **({"title": squash(out["title"])} if title else {})}


def markdown(lines: list[str], heads: list[str], title: str | None) -> str:
    """평문 → 마크다운: 제목은 #, 구역 머리는 ##, 탭 표는 파이프 표, 예제 구역은 코드 울타리."""
    out, fence, before = [], False, False
    for line in lines:
        if fence and not line.strip():
            out.append("```")
            fence = False
        tab = "\t" in line
        if line == title:
            out.append("# " + line)
        elif line in heads:
            out.append("## " + line)
            if line.startswith(("예제", "Sample")):
                out.append("```")
                fence = True
        elif tab:
            cells = line.split("\t")
            out.append("| " + " | ".join(cells) + " |")
            if not before:
                out.append("|" + "---|" * len(cells))
        else:
            out.append(line)
        before = tab
    return "\n".join(out + (["```"] if fence else []))


def plain_text(lines: list[str]) -> str:
    """마크다운 → 평문: # 떼기, 파이프 표는 탭 표로, 구분 줄과 코드 울타리는 뺀다."""
    out = []
    for line in lines:
        if line.startswith("```") or re.fullmatch(r"\|[-:| ]+\|", line):
            continue
        if line.startswith("|"):
            line = "\t".join(cell.strip() for cell in line.strip("|").split("|"))
        out.append(re.sub(r"^#+\s+", "", line))
    return "\n".join(out)


def variants(row: dict):
    """(이름, 바꾼 글): 줄 끝(CRLF, 외톨이 CR), 빈칸(NBSP, 전각 공백, 폭 없는 공백·BOM), 앞 두 구역 순서, 잡음 넣기, 마크다운↔평문."""
    raw, heads = row["raw"], row["heads"]
    lines = raw.split("\n")
    at = [lines.index(head) for head in heads[:3]]
    yield "crlf", raw.replace("\n", "\r\n")
    yield "cr", "".join(line + ("\r" if n % 2 and lines[n + 1] else "\n") for n, line in enumerate(lines[:-1])) + lines[-1]
    yield "nbsp", raw.replace(" ", " ")
    yield "wide", raw.replace(" ", "　")
    yield "zero", "﻿" + "\n".join("​" + line if line else line for line in lines).replace(", ", ",​ ")
    yield "order", "\n".join(lines[:at[0]] + lines[at[1]:at[2]] + lines[at[0]:at[1]] + lines[at[2]:])
    yield "noise", "\n".join(NOISE_TOP + lines[:at[1]] + NOISE_MID + lines[at[1]:] + NOISE_END)
    yield "markdown", plain_text(lines) if raw.startswith("#") else markdown(lines, heads, row["expect"]["title"])


def ingest_corpus() -> None:
    """문제 넣기 감지의 규칙 층(모델 0회, /api/problems/detect): 시험 자료마다 문제인가·방식·인자 이름·케이스·줄마다 구역·수 범위가 기대와 같고,
    잡음 줄이 뽑은 케이스·범위에 섞이지 않는다. 규칙은 '답이 여럿'을 글의 낱말로 짐작하지 않는다. 키가 없으면 fast가 아니어도 같은 결과다.
    줄 끝·빈칸·구역 순서·잡음·마크다운 변형에도 결과가 같다. 50KB 글도 2초 안(목표 200ms. 잰 값은 CI 작업 요약에 남긴다)."""
    rows = corpus()
    assert {"F01", "F02", "F03", "F04", "F05", "F08a", "F08b", "F08c", "F08d", "F09", "F10", "F11", "F13", "F16", "F18"} <= {row["id"] for row in rows}
    assert "글이어야" in refuses("/api/problems/detect", text=["x"])
    bad = []
    for row in rows:
        raw, want, where = row["raw"], row["expect"], row["id"]
        out = detect(raw, fast=True)
        if detect(raw) != out:
            bad.append((where, "키 없이 fast가 아닐 때 결과가 다르다"))
        if out["problem"] is not (want["verdict"] == "problem") or (NOT_PROBLEM in out["notice"]) is out["problem"]:
            bad.append((where, "문제인가", out["problem"], out["notice"]))
        if want["mode"] and (out["mode"], out["names"]) != (want["mode"], want["names"]):
            bad.append((where, "방식·이름", out["mode"], out["names"]))
        if trimmed(out["cases"]) != want["cases"]:
            bad.append((where, "케이스", out["cases"]))
        if want["title"] is not None and squash(out["title"]) != squash(want["title"]):
            bad.append((where, "제목", out["title"]))
        if out["many"] is not False:
            bad.append((where, "규칙이 답이 여럿을 짐작했다"))
        if "skipped" in want and (out["skipped"], out.get("missed", [])) != (want["skipped"], want["missed"]):
            bad.append((where, "읽지 못한 줄", out["skipped"], out.get("missed")))
        for kind, pieces in want["sections"].items():
            bad += [(where, "구역", piece, kind, out["kinds"][line_at(raw, piece) - 1]) for piece in pieces if out["kinds"][line_at(raw, piece) - 1] != kind]
        bounds = [squash(line) for line in out["bounds"]]
        bad += [(where, "범위 없음", line) for line in want["bounds"] if not any(squash(line) in got for got in bounds)]
        values = squash(json.dumps(out["cases"], ensure_ascii=False))
        bad += [(where, "잡음이 섞임", line) for line in want["absent"] if squash(line) in values or any(squash(line) in got for got in bounds)]
    for row in rows:  # 변형 불변(F14). 잡음을 넣은 글의 제목은 모델이 정한다
        if "heads" not in row:
            continue
        keep = row["expect"]["title"] is not None
        base = summary(detect(row["raw"], fast=True), keep)
        for name, text in variants(row):
            got = summary(detect(text, fast=True), keep and name != "noise")
            if got != {key: value for key, value in base.items() if key in got}:
                bad.append((row["id"], "변형", name, {key: value for key, value in got.items() if base.get(key) != value}))
    assert not bad, "\n".join(map(str, bad))

    f01 = next(row for row in rows if row["id"] == "F01")
    big, n = f01["raw"] + "\n\n\n댓글", 0  # 댓글이 아주 긴 50KB 글(F15)
    while len(big.encode("utf-8")) < 50 * 1024:
        n += 1
        big += f"\n방문자{n}: 저는 앞에서부터 하루씩 세면서 풀었는데 예제 {n % 3 + 1}에서 막혔어요. " + "다시 읽어 보니 이해가 됐어요. " * 8
    took = []
    for body in ({"fast": True}, {}):
        started = time.perf_counter()
        out = call("/api/problems/detect", text=big, **body)[1]
        took.append(time.perf_counter() - started)
        assert (out["mode"], trimmed(out["cases"])) == ("function", f01["expect"]["cases"]), out["cases"]
    assert max(took) < 2.0, took
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary_file:
            summary_file.write(f"### 문제 넣기 감지(규칙만)\n- {len(big.encode('utf-8')) // 1024}KB 글: {max(took) * 1000:.0f}ms (목표 200ms)\n")


class JsonLlm(FakeLlm):
    """구획 나누기 응답을 설계의 JSON 꼴(dict)로 적어 둔다. 꼴 없이(글로) 부르는 쪽에는 같은 내용을 JSON 글로 준다."""

    def run(self, task, messages, schema, images=None, params=None):
        queue = self.scripts.get(task)
        if schema is None and queue and isinstance(queue[0], dict):
            queue[0] = json.dumps(queue[0], ensure_ascii=False)
        return super().run(task, messages, schema, images, params)


def outline(**fields) -> dict:
    """구획 나누기(task ingest.outline) 응답 한 벌. 줄 번호는 1부터, 구간은 [처음, 끝](양 끝 포함), samples의 in·out은 머리 줄을 뺀 내용 줄."""
    return {"problem": True, "title": None, "body": [], "samples": [], "table": None, "cases": [], "noise": [], "mode": "function", "names": [], "many": False, **fields}


def spans(numbers) -> list[list[int]]:
    out = []
    for n in sorted(numbers):
        if out and out[-1][1] == n - 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return out


def with_model(text: str, *answers, **body) -> tuple[dict, list]:
    """AI가 연결된 것처럼 두고 감지를 한 번 부른다(구획 나누기는 answers를 차례로 받는다). (응답, 모델 호출 기록)."""
    fake = JsonLlm({"ingest.outline": list(answers)})
    with use_llm(fake), patch.object(server, "connected", lambda: True):
        return detect(text, **body), fake.calls


def detect_model() -> None:
    """감지에 구획 나누기(작은 급, task ingest.outline)를 합친다(가짜 모델). 줄에 글자 그대로 없거나 값으로 읽히지 않는 케이스는 버리고,
    범위 밖·겹친 구간이나 60%를 넘는 잡음은 결과 전체를 버린다(가운데 급 한 번 뒤 규칙만). 규칙이 예시를 깨끗이 읽었으면 규칙의 예시·방식이 이긴다.
    모델이 실패하면 규칙 결과 그대로. 문제가 아니라고 하면 알리고 뒤 준비를 돌리지 않는다. 사용자가 고친 칸(touched)은 덮지 않고 suggest로만 준다.
    키가 없거나 fast면 모델 0회. 글 속의 지시에도 응답의 꼴이 그대로이고 모델이 쓴 글이 실리지 않는다."""
    from tutor.llm import LlmFailed, LlmTimeout, themes

    rows = {row["id"]: row for row in corpus()}
    small, middle = themes.model_of("small"), themes.model_of("middle")
    assert themes.pick("ingest.outline")[0] == small

    # 잡음 섞인 글(F03): 모델이 짚은 잡음 줄만 noise가 되고, 남을 줄의 구역과 규칙의 케이스는 그대로. 제목은 모델이 짚은 줄. 작은 급 한 번
    f03 = rows["F03"]
    raw3, absent = f03["raw"], f03["expect"]["absent"]
    n3, title3 = len(raw3.splitlines()), line_at(raw3, "연속 출석 보상", whole=True)
    fast3 = detect(raw3, fast=True)
    good3 = outline(title=title3, noise=spans(line_at(raw3, line, whole=True) for line in absent), names=["days", "k"])
    out, calls = with_model(raw3, good3)
    assert [(c["task"], c["params"].get("model")) for c in calls] == [("ingest.outline", small)], calls
    noisy = {line_at(raw3, line, whole=True) - 1 for line in absent}
    assert {i for i, line in enumerate(raw3.splitlines()) if line.strip() and out["kinds"][i] == "noise"} == noisy, out["kinds"]
    for kind, pieces in f03["expect"]["sections"].items():
        for piece in pieces:
            assert out["kinds"][line_at(raw3, piece) - 1] == fast3["kinds"][line_at(raw3, piece) - 1] == kind, (piece, kind)
    assert (out["title"], out["mode"], out["names"], trimmed(out["cases"])) == ("연속 출석 보상", "function", ["days", "k"], f03["expect"]["cases"]), out
    assert (out["problem"], out["notice"], out["suggest"]) == (True, "", {}), out

    # (j) 실패하거나 검사에 걸리면 가운데 급으로 한 번 더(다른 task 없이)
    for first in (LlmFailed("모양이 맞지 않습니다."), outline(title=title3, noise=[[1, 2], [2, 3]])):
        out, calls = with_model(raw3, first, good3)
        assert [(c["task"], c["params"].get("model")) for c in calls] == [("ingest.outline", small), ("ingest.outline", middle)], calls
        assert out["title"] == "연속 출석 보상" and out["kinds"][line_at(raw3, absent[0], whole=True) - 1] == "noise", out

    # (e) 두 번 다 실패: 규칙 결과 그대로, 호출은 두 번까지
    for answers in ((LlmFailed("x"), LlmFailed("x")), (LlmTimeout("x"), LlmTimeout("x")), ("이 글은 JSON이 아니다", "[]")):
        out, calls = with_model(raw3, *answers)
        assert out == fast3 and 1 <= len(calls) <= 2, (answers, len(calls))
    assert len(with_model(raw3, LlmFailed("x"), LlmFailed("x"))[1]) == 2

    # (b) 범위 밖·거꾸로·겹친 구간, 없는 제목 줄 / (c) 잡음이 60%를 넘음: 결과 전체를 버린다(두 번 다 그러면 규칙만)
    heavy = -(-n3 * 3 // 4)
    for bad in (outline(title=title3, noise=[[1, 2], [2, 3]]), outline(title=title3, noise=[[n3 - 1, n3 + 5]]), outline(title=title3, noise=[[0, 1]]),
                outline(title=title3, noise=[[5, 4]]), outline(title=n3 + 3), outline(title=title3, body=[[4, 9]], noise=[[8, 9]]),
                outline(title=title3, noise=[[n3 - heavy + 1, n3]])):
        out, _ = with_model(raw3, bad, bad)
        assert out == fast3 and "noise" not in out["kinds"], bad

    # (d) 규칙이 예시를 깨끗이 읽었으면 규칙의 케이스·방식·이름이 이긴다. 함수 방식에는 '답이 여럿'을 켜지 않는다
    f01 = rows["F01"]
    raw1 = f01["raw"]
    row1, notes = line_at(raw1, "[1, 1, 1, 1]"), [line_at(raw1, "입출력 예 설명", whole=True), len(raw1.splitlines())]
    out, _ = with_model(raw1, outline(title=1, mode="program", names=["a", "b"], table=notes, many=True,
                                      cases=[{"line": row1, "args": ["[1, 1, 1, 1]", "4"], "expected": "4"}]))
    assert (out["mode"], out["names"], trimmed(out["cases"]), out["many"]) == ("function", ["days", "k"], f01["expect"]["cases"], False), out

    # 깨끗하지 않으면(빈 줄 하나 뒤 댓글을 예제 출력으로 삼킴) 모델이 짚은 예제 구간을 기존 규칙으로 읽는다
    raw2 = rows["F02"]["raw"] + "\n\n댓글 2\n방문자1: 예제 2를 보고 이해했어요.\n방문자2: D가 0이면 같은 밝기끼리만 묶여요."
    assert "spill" in detect(raw2, fast=True)
    lines2 = raw2.splitlines()

    def block(head: str) -> list[int]:  # 머리 다음 줄부터 빈 줄 앞까지
        start = end = line_at(raw2, head, whole=True)
        while end < len(lines2) and lines2[end].strip():
            end += 1
        return [start + 1, end]

    samples = [{"in": block(f"예제 입력 {n} 복사"), "out": block(f"예제 출력 {n} 복사")} for n in (1, 2)]
    out, _ = with_model(raw2, outline(title=1, mode="program", samples=samples, noise=[[line_at(raw2, "댓글 2", whole=True), len(lines2)]]))
    assert (out["mode"], trimmed(out["cases"])) == ("program", rows["F02"]["expect"]["cases"]) and "spill" not in out, out
    assert out["kinds"][-1] == "noise"

    # (a) 문장으로 적힌 예시: 규칙은 못 읽는다. 모델 케이스는 그 줄에 글자 그대로 있고 값으로 읽히는 것만 남는다. 제목·잡음도 채운다
    text = "\n".join(["목록으로 돌아가기", "줄 세우기 비용", "", "문제 설명",
                      "학생들의 키가 적힌 배열 heights와 정수 d가 주어집니다. 이웃한 두 학생의 키 차이가 d를 넘는 곳마다 비용이 1 듭니다.",
                      "드는 비용의 합을 return 하세요.", "예를 들어 heights가 [3, 1, 2]이고 d가 1이면 답은 1입니다.",
                      "heights가 [1, 2, 3]이고 d가 2이면 키 차이가 모두 작아 답은 0입니다.", "", "제한사항", "1 ≤ heights의 길이 ≤ 1,000", "1 ≤ d ≤ 1,000"])
    fast = detect(text, fast=True)
    assert fast["cases"] == [] and fast["problem"], fast
    e1, e2 = line_at(text, "[3, 1, 2]"), line_at(text, "[1, 2, 3]")
    said = outline(title=line_at(text, "줄 세우기 비용", whole=True), names=["heights", "d"], noise=[[1, 1]], cases=[
        {"line": e1, "args": ["[3, 1, 2]", "1"], "expected": "1"}, {"line": e2, "args": ["[1, 2, 3]", "2"], "expected": "0"},
        {"line": e1, "args": ["[9, 9]", "1"], "expected": "0"},  # 그 줄에 없는 값
        {"line": e2, "args": ["[1, 2, 3]", "2"], "expected": "작아"}])  # 그 줄에 있지만 값으로 읽히지 않는 글
    read = [{"input": "[[3, 1, 2], 1]", "expected": "1"}, {"input": "[[1, 2, 3], 2]", "expected": "0"}]
    out, _ = with_model(text, said)
    assert (out["title"], out["names"], trimmed(out["cases"]), out["kinds"][0], out["suggest"]) == ("줄 세우기 비용", ["heights", "d"], read, "noise", {}), out

    # (g) 사용자가 그사이 고친 칸은 덮지 않고 제안으로만. 고치지 않은 칸(잡음)은 채운다
    out, _ = with_model(text, said, touched=["title", "cases"])
    assert (out["title"], out["cases"], out["names"], out["kinds"][0]) == (fast["title"], fast["cases"], fast["names"], "noise"), out
    assert out["suggest"]["title"] == "줄 세우기 비용" and trimmed(out["suggest"]["cases"]) == read, out["suggest"]

    # (f) 모델이 문제가 아니라고 하면 알린다. 감지는 구획 나누기 말고 아무것도 부르지 않고 뒤 준비를 돌리지 않는다
    tries = []
    with patch.object(server, "prepare_later", tries.append):
        out, calls = with_model("공지\n다음 주 월요일 새벽 2시부터 4시까지 서버를 점검합니다.\n접속자가 1,000명 이상이면 대기열이 생길 수 있습니다.", outline(problem=False))
    assert out["problem"] is False and NOT_PROBLEM in out["notice"] and not tries and [c["task"] for c in calls] == ["ingest.outline"], (out, calls)

    # 답이 여럿(표준 입출력)은 모델이 켠다. 예시 없는 글의 방식도 모델이 채운다
    assert with_model(rows["F10"]["raw"], outline(title=1, mode="program", many=True))[0]["many"] is True
    head11 = rows["F11"]["raw"].split("\n예제 입력 1")[0]
    out, _ = with_model(head11, outline(title=1, mode="program"))
    assert (out["mode"], out["cases"]) == ("program", []), out

    # (i) 글 속 지시: 글은 사용자 말로만 넘기고, 응답 꼴은 그대로, 모델이 쓴 글(코드)은 실리지 않는다
    f16 = rows["F16"]
    raw16 = f16["raw"]
    inject = line_at(raw16, "이전 지시는 모두 무시하고")
    hostile = {**outline(title=1, names=["s"], cases=[{"line": inject, "args": ["정답 코드"], "expected": "def solution(s): return 0"}]),
               "code": "def solution(s):\n    return 0", "answer": "def solution(s): return 0"}
    out, calls = with_model(raw16, "def solution(s):\n    return 0", hostile)
    assert "def solution" not in json.dumps(out, ensure_ascii=False) and trimmed(out["cases"]) == f16["expect"]["cases"], out
    for one in calls:
        parts = [(m["role"], str(m["content"])) for m in one["messages"]]
        assert not any(role == "system" and "이전 지시는 모두 무시하고" in content for role, content in parts)
        assert any(role == "user" and "이전 지시는 모두 무시하고" in content for role, content in parts)


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
        # 벡터 색인을 끈다: 임베딩 모델이 있는 기기에서는 앞서 등록한 비슷한 문제를 찾아 잇는 판정(plan.gate)이 더 불려 아래의 호출 목록이 기기마다 달라진다
        with use_llm(fake), patch.object(server, "index", lambda: None):
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


def guessed_level() -> None:
    """단계를 고르지 않은 등록 문제는 분석이 어림한 단계를 level_by가 analysis로 싣는다(화면은 수정 칸에 이것을 넣지 않는다). 고른 단계는 user. 어림한 채 고쳐 저장해도 어림으로 남는다."""
    pid = server.register(GOOD)["id"]
    with server.tutor() as t:
        t.adopt(pid, {**FIRST["ready"], "fact": {**FIRST["ready"]["fact"], "level": 2}})  # 분석이 어림한 단계
    state = call("/api/state", id=pid)[1]["problem"]
    assert state["level"] == 2 and state["level_by"] == "analysis", (state["level"], state["level_by"])
    call("/api/problems/edit", id=pid, title="두 수의 합", text=GOOD["text"], cases=GOOD["cases"][:1] + GOOD["cases"][2:], level=0)  # 수정 칸이 비어 있으면 0을 보낸다
    assert call("/api/state", id=pid)[1]["problem"]["level_by"] == "analysis"
    call("/api/problems/edit", id=pid, title="두 수의 합", text=GOOD["text"], cases=GOOD["cases"][:1] + GOOD["cases"][2:], level=4)
    state = call("/api/state", id=pid)[1]["problem"]
    assert (state["level"], state["level_by"]) == (4, "user"), state
    # 배지는 누가 단계를 붙였는지와 상관없이 같은 겉모습이다: 화면과 문서에 어림 표시가 없다
    root = HERE.parent.parent
    assert "어림" not in (HERE / "app.js").read_text(encoding="utf-8")
    assert "어림" not in (root / "Docs" / "guide" / "add-problem.md").read_text(encoding="utf-8")


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
    assert (sol["code"], sol["language"], sol["verified"], sol["next"], sol["traps"]) == (CODE, "python", False, None, [])  # 언어 함정은 기본 문제에만(증명이 없다)
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


def prep_unverified() -> None:
    """준비가 끝났는데 풀이 가이드를 얻지 못했으면(고친 예시를 통과하는 풀이가 없는 문제 등) 검증하지 못함과 까닭이 남는다. 이미 대조 결과가 있으면 덮지 않는다."""
    import time
    from tutor.main import Outcome

    pid = server.register(GOOD)["id"]
    def prepare_and_wait():
        call("/api/state", id=pid, open=True)
        for _ in range(200):
            if pid not in server.PREPARING:
                break
            time.sleep(0.02)
        return call("/api/state", id=pid)[1]["problem"]
    with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", lambda self, problem_id: Outcome(200, {"blocks": 0, "patterns": []})):
        before = call("/api/state", id=pid)[1]["problem"]
        assert before["verified"] == "" and not before["preparing"], before  # 준비 전에는 줄이 비어 있다
        body = prepare_and_wait()
        assert body["verified"] == "none" and body["check"]["why"] == server.UNVERIFIED["why"] and not body["prepare_failed"], body
        server.PREPARED.discard(pid)
        server.cross_done(pid, {"verified": "all", "calls": 2, "tiers": ["middle"], "doubts": [], "why": "", "hidden": 3, "efficiency": 0})
        assert prepare_and_wait()["verified"] == "all"  # 앞의 대조 결과를 '검증하지 못함'으로 덮지 않는다


def two_step_helpers():
    """두 걸음 준비 시험의 바탕: 뒤에서 도는 대조(Tutor.recheck)를 가짜로 바꿔 끼우고, 끝난 뒤 조용해질 때까지 기다린다."""
    import threading
    import time

    def quiet(pid, entered):
        assert entered.wait(10), "대조가 시작되지 않았다"
        calm = 0
        for _ in range(400):
            body = call("/api/state", id=pid)[1]["problem"]
            calm = calm + 1 if pid not in server.PREPARING and not body.get("preparing") and not body.get("checking") else 0
            if calm >= 4:
                return
            time.sleep(0.05)
        raise AssertionError("준비가 끝나지 않았다")

    def forget():
        for held in (server.PREPARED, server.RECHECKED, server.PREPARING, server.PREP_FAILED, server.CHECKING):
            held.clear()

    return threading, quiet, forget


def two_step_start_is_free() -> None:
    """등록 문제의 준비는 두 걸음이다. 1걸음(가이드·블록)이 끝나면 2걸음(대조·숨은 테스트)이 길게 도는 동안에도 튜터 시작은 기다리지 않고 모델도 부르지 않는다."""
    from tutor.main import Outcome

    threading, quiet, forget = two_step_helpers()
    pid = server.register(GOOD)["id"]
    entered, release = threading.Event(), threading.Event()

    def prepare(self, problem_id):
        assert self.adopt(problem_id, own_ready("def solution(a, b):\n    return a + b"))  # 1걸음: 가이드·블록을 저장한다
        return Outcome(200, {"blocks": 1, "patterns": []})

    def recheck(self, problem_id):
        entered.set()  # 2걸음의 긴 구간(모델 호출·실행)을 흉내 낸다
        assert release.wait(30)
        return None

    fake, answered = FakeLlm({}), []

    def start():
        with use_llm(fake):
            answered.append(call("/api/turn", id=pid, mode="chair", event="start"))

    try:
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", prepare), patch.object(server.Tutor, "recheck", recheck):
            call("/api/state", id=pid, open=True)
            assert entered.wait(10), "1걸음 뒤에 2걸음이 이어지지 않았다"
            assert call("/api/state", id=pid)[1]["problem"].get("checking") is True  # 숨은 테스트를 만드는 중
            worker = threading.Thread(target=start, daemon=True)
            worker.start()
            worker.join(5)
            assert not worker.is_alive(), "튜터 시작이 2걸음을 기다린다"
            assert answered[0][0] == 200 and not fake.calls, (answered, fake.calls)
            release.set()
            quiet(pid, entered)
    finally:
        release.set()
        forget()
        call("/api/problems/delete", id=pid)


def two_step_checking_state() -> None:
    """2걸음은 preparing이 아니라 checking(숨은 테스트 만드는 중)으로 보이고, 1걸음(가이드·블록 준비)은 preparing으로 보인다."""
    from tutor.main import Outcome

    threading, quiet, forget = two_step_helpers()
    pid = server.register(GOOD)["id"]
    in_prepare, in_recheck, release, release_check = threading.Event(), threading.Event(), threading.Event(), threading.Event()

    def prepare(self, problem_id):
        in_prepare.set()
        assert release.wait(30)
        assert self.adopt(problem_id, own_ready("def solution(a, b):\n    return a + b"))
        return Outcome(200, {"blocks": 1, "patterns": []})

    def recheck(self, problem_id):
        in_recheck.set()
        assert release_check.wait(30)  # 1걸음을 놓아준 뒤에도 2걸음은 따로 붙잡아 둔다
        return None

    try:
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", prepare), patch.object(server.Tutor, "recheck", recheck):
            call("/api/state", id=pid, open=True)
            assert in_prepare.wait(10)
            body = call("/api/state", id=pid)[1]["problem"]
            assert body["preparing"] and not body.get("checking"), body
            release.set()
            assert in_recheck.wait(10)
            body = call("/api/state", id=pid)[1]["problem"]
            assert body.get("checking") is True and not body["preparing"], body
            release_check.set()
            quiet(pid, in_recheck)
            body = call("/api/state", id=pid)[1]["problem"]
            assert not body.get("checking") and not body["preparing"], body
    finally:
        release.set()
        release_check.set()
        forget()
        call("/api/problems/delete", id=pid)


def two_step_keeps_talk() -> None:
    """2걸음이 풀이를 바꿨을 때: 대화가 이미 시작됐으면 대화·블록 진행을 지우지 않고 풀이도 그대로 두며 '다시 준비' 표시만 남긴다. 대화가 없으면 새 풀이로 바꿔 끼운다."""
    from tutor.main import Outcome
    from tutor.state import Solution

    threading, quiet, forget = two_step_helpers()
    old = "def solution(a, b):\n    return a + b"
    new = Solution("더한다.", ["더한다"], "def solution(a, b):\n    return b + a", True, [])
    entered = threading.Event()

    def recheck(self, problem_id):
        entered.set()
        return new

    def prepare(self, problem_id):
        return Outcome(200, {"blocks": 1, "patterns": []})

    def counts(pid):
        with server.tutor() as t:
            return [t.store.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE problem_id=?", (pid,)).fetchone()[0] for table in ("message", "block_state")], t.store.load(pid).solution.code

    talked, fresh = server.register(GOOD)["id"], server.register({**GOOD, "title": "두 수의 합 둘"})["id"]
    try:
        for pid in (talked, fresh):
            with server.tutor() as t:
                t.adopt(pid, own_ready(old))
        with use_llm(FakeLlm({})):
            call("/api/turn", id=talked, mode="chair", event="start")  # 대화가 시작됐다
        server.write_json(server.BLOCKS_FILE, {**server.read_json(server.BLOCKS_FILE, {}), talked: {"b1": {"code": "x", "by": "me"}}})
        before = counts(talked)
        assert before[0][0] > 0
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "recheck", recheck), patch.object(server.Tutor, "prepare", prepare):
            call("/api/state", id=talked, open=True)
            quiet(talked, entered)
            assert counts(talked) == before, (counts(talked), before)  # 대화·블록 진행·풀이 모두 그대로
            assert server.read_json(server.BLOCKS_FILE, {}).get(talked) == {"b1": {"code": "x", "by": "me"}}
            assert call("/api/state", id=talked)[1]["problem"]["better"] is True  # 문제 머리에 '다시 준비'가 뜬다
            assert call("/api/swap", id=talked) == (200, {"ok": True})  # 누르면 그때 바꿔 끼운다(대화는 처음부터)
            quiet(talked, entered)
            assert counts(talked) == ([0, 0], new.code) and not call("/api/state", id=talked)[1]["problem"]["better"], counts(talked)
            entered.clear()
            call("/api/state", id=fresh, open=True)
            quiet(fresh, entered)
            assert counts(fresh)[1] == new.code  # 대화가 없으면 바꿔 끼운다
    finally:
        forget()
        for pid in (talked, fresh):
            call("/api/problems/delete", id=pid)


def two_step_restart() -> None:
    """앱을 1·2걸음 사이에 끄면(2걸음이 끝나기 전에 서버를 새로 만든 꼴) 다시 열 때 대조가 돈다. 대조 결과는 저장소에 남지 않았다."""
    threading, quiet, forget = two_step_helpers()
    pid = server.register(GOOD)["id"]
    entered, runs = threading.Event(), []

    def recheck(self, problem_id):
        runs.append(problem_id)
        entered.set()
        raise RuntimeError("앱이 꺼졌다")  # 2걸음이 끝나지 못했다

    import contextlib
    import io
    try:
        with server.tutor() as t:
            t.adopt(pid, own_ready("def solution(a, b):\n    return a + b"))  # 1걸음이 끝난 상태
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "recheck", recheck), contextlib.redirect_stderr(io.StringIO()):
            call("/api/state", id=pid, open=True)
            quiet(pid, entered)
            assert runs == [pid] and call("/api/state", id=pid)[1]["problem"]["verified"] == ""
            forget()  # 서버를 새로 만든 꼴: 메모리의 상태가 없고 저장소만 남는다
            entered.clear()
            call("/api/state", id=pid, open=True)
            quiet(pid, entered)
            assert runs == [pid, pid], runs  # 다시 열 때 대조가 돈다
    finally:
        forget()
        call("/api/problems/delete", id=pid)


def two_step_overlap() -> None:
    """2걸음이 도는 동안 글을 고치면 새 준비의 2걸음이 하나 더 돈다. 먼저 시작한 옛 2걸음이 끝나도 새 2걸음이 도는 동안은 checking이 참이고, 둘 다 끝나야 거짓이다."""
    from tutor.main import Outcome

    threading, quiet, forget = two_step_helpers()
    pid = server.register(GOOD)["id"]
    gates, started, workers = [threading.Event(), threading.Event()], [threading.Event(), threading.Event()], []

    def prepare(self, problem_id):
        assert self.adopt(problem_id, own_ready("def solution(a, b):\n    return a + b"))
        return Outcome(200, {"blocks": 1, "patterns": []})

    def recheck(self, problem_id, **kept):
        n = len(workers)
        workers.append(threading.current_thread())
        started[n].set()
        assert gates[n].wait(30)
        return None

    def checking():
        return call("/api/state", id=pid)[1]["problem"]["checking"]

    try:
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True), patch.object(server.Tutor, "prepare", prepare), patch.object(server.Tutor, "recheck", recheck):
            call("/api/state", id=pid, open=True)
            assert started[0].wait(10), "1걸음 뒤에 2걸음이 이어지지 않았다"
            call("/api/problems/edit", id=pid, **{**GOOD, "text": GOOD["text"] + " 음수도 들어온다."})  # 2걸음이 붙잡힌 동안 글을 고친다: 새 준비가 돈다
            assert started[1].wait(10), "글을 고친 뒤 새 2걸음이 돌지 않았다"
            gates[0].set()  # 옛 2걸음만 끝낸다
            workers[0].join(10)
            assert not workers[0].is_alive() and checking() is True  # 새 2걸음이 아직 돈다
            gates[1].set()
            workers[1].join(10)
            assert not workers[1].is_alive() and checking() is False
    finally:
        for gate in gates:
            gate.set()
        forget()
        call("/api/problems/delete", id=pid)


def two_step_pending() -> None:
    """1걸음이 맡긴 채점 결과와 쓴 급(pending)은 앱을 껐다 켜도 남아, 2걸음의 대조 결과에 맞지 않은 예시와 급으로 적힌다. 대조가 끝나면 지운다."""
    threading, quiet, forget = two_step_helpers()
    pid = server.register(GOOD)["id"]
    ready = own_ready("def solution(a, b):\n    return a - b")
    ready["solution"]["verified"] = False  # 세 번 다 예시를 못 맞힌 가이드
    try:
        with server.tutor() as t:
            assert t.adopt(pid, ready)
        server.cross_later(pid, {"status": "failed", "cases": [{"id": "1", "kind": "example", "input": "[1, 2]", "expected": "3", "got": "-1", "status": "failed"},
                                                               {"id": "2", "kind": "example", "input": "[5, 5]", "expected": "10", "got": "0", "status": "failed"}]}, ["small", "middle", "large"])
        forget()  # 1걸음 뒤에 앱을 껐다 켠 꼴: 메모리는 비고 problems.json만 남는다
        done = threading.Event()
        done.set()
        with patch.object(server, "PREPARE", True), patch.object(server, "connected", lambda: True):
            call("/api/state", id=pid, open=True)
            quiet(pid, done)
        body = call("/api/state", id=pid)[1]["problem"]
        assert body["verified"] == "none" and body["check"]["tiers"] == ["small", "middle", "large"], body["check"]
        assert [row["where"] for row in body["check"]["doubts"]] == ["예시 1", "예시 2"], body["check"]
        assert not getattr(server.PROBLEMS[pid], "pending", None)
    finally:
        forget()
        call("/api/problems/delete", id=pid)

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
    from tutor.common.talk_rules import ALONE_OK

    def text(parts):  # 블록 주석과 빈 줄을 뺀 글
        return "\n".join(row for _, part in parts for row in part.split("\n") if row.strip() and not row.strip().startswith("# 블록"))

    b1 = "\n".join(row[4:] for row in LINES[1:5])
    parts = call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": b1, "by": "me"}, "b2": {"code": "\n".join(LINES[5:]), "by": "tutor"}})[1]["parts"]
    assert [i for i, _ in parts] == [0, 1] and parts[0][1].startswith("def solution(loans, k):\n    # 블록 1 · ") and text(parts) == CODE, parts
    parts = call("/api/compose", id=PID, mode="guide", blocks={"b1": {"code": "  ", "by": "me"}, "b2": {"code": "return []", "by": "me"}})[1]["parts"]
    assert [i for i, _ in parts] == [0, 1] and parts[0][1] == "def solution(loans, k):" and parts[1][1].endswith(" return []"), parts  # 빈 블록은 틀 줄만(머리가 빠지면 함수 밖의 return이었다)
    # 튜터가 '남은 블록은 건너뛰어도 된다'고 한 뒤의 빈 블록은 화면이 모으기에서 막지 않는다(화면은 그 말로 안다)
    assert ALONE_OK.split(".")[0] in (Path(__file__).parent / "app.js").read_text(encoding="utf-8")
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


def key_flow() -> None:
    """API 키: 그 공급자의 키 꼴이 아니면(빈칸·한글·다른 접두사) 저장하지 않고 까닭을 말한다. 지우기는 그 공급자의 키만, 화면에서 넣은 것만 지운다."""
    claude, openai = "sk-ant-api03-" + "a" * 20, "sk-proj-" + "b" * 20
    with patch.dict(os.environ, {}), patch.object(server.keycheck, "check", lambda provider, key, **kw: server.keycheck.OK):  # 확인은 아래 key_check_flow에서 따로 본다(네트워크를 쓰지 않는다)
        for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            os.environ.pop(name, None)
        for name, bad in (("claude", "hello world 한글"), ("claude", "sk-ant-abc def"), ("claude", openai), ("openai", "sk-a b"), ("openai", "한글키"), ("openai", claude), ("openai", "abcdef")):
            assert "꼴이 아니에요" in refuses("/api/key", name=name, value=bad) and bad not in refuses("/api/key", name=name, value=bad)  # 값은 글에 싣지 않는다
        assert not server.KEY_FILE.exists() and not any(os.environ.get(env) for env in server.KEYS.values())  # 거절한 키는 파일에도 환경에도 없다
        assert call("/api/key", name="claude", value=claude)[1]["keys"] == {"claude": True, "openai": False}
        assert call("/api/key", name="openai", value=openai)[1]["keys"] == {"claude": True, "openai": True}
        assert refuses("/api/key/delete", name="x") and refuses("/api/key/delete", name=["claude"])
        after = call("/api/key/delete", name="openai")[1]["keys"]  # 지운 공급자만 빠진다
        assert after == {"claude": True, "openai": False} and server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": claude}
        # 키 파일은 처음부터 소유자만 읽게 만든다(남은 임시 파일의 권한도 따르지 않는다). 넣기·지우기가 겹쳐도 한쪽 변경이 사라지지 않는다
        modes = []
        real_open = os.open
        tmp = server.KEY_FILE.with_suffix(".tmp")
        tmp.write_text("{}", encoding="utf-8")
        tmp.chmod(0o644)
        with patch.object(server.os, "open", lambda path, flags, mode=0o777: modes.append(mode) or real_open(path, flags, mode)):
            server.save_key("ANTHROPIC_API_KEY", claude)
        assert modes == [0o600], modes
        if os.name != "nt":
            assert server.KEY_FILE.stat().st_mode & 0o777 == 0o600
        import threading
        threads = [threading.Thread(target=server.save_key, args=(f"K{n}", "v")) for n in range(8)]
        for one in threads:
            one.start()
        for one in threads:
            one.join()
        assert set(server.read_json(server.KEY_FILE, {})) == {"ANTHROPIC_API_KEY", *(f"K{n}" for n in range(8))}
        for n in range(8):
            server.drop_key(f"K{n}")
        assert server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": claude}
        with patch.object(server.os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("디스크가 찼다"))):  # 쓰다가 실패하면 원래 키 파일이 그대로다
            try:
                server.save_key("OPENAI_API_KEY", openai)
                raise AssertionError("쓰기 실패는 알려야 한다")
            except OSError:
                pass
        assert server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": claude} and not server.KEY_FILE.with_suffix(".tmp").exists()
        with patch.object(server.Path, "replace", lambda self, target: (_ for _ in ()).throw(OSError("바꿔 넣지 못했다"))):  # 바꿔 넣기가 실패해도 같다
            try:
                server.save_key("OPENAI_API_KEY", openai)
                raise AssertionError("바꿔 넣기 실패는 알려야 한다")
            except OSError:
                pass
        assert server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": claude} and not server.KEY_FILE.with_suffix(".tmp").exists()
        try:
            call("/api/key/delete", name="openai")
            raise AssertionError("넣지 않은 키를 지울 수는 없다")
        except server.Refuse as exc:
            assert exc.status == 409 and exc.code == "key_outside", exc  # 화면에서 넣은 것이 아니면 환경(.env)은 건드리지 않는다
        env_file = server.DATA / ".env"  # .env에도 같은 공급자의 키가 있으면: 지운 뒤에는 그 키로 연결된 채이고, 지울 수 있는 키(keys_saved)는 아니다
        env_file.write_text("OPENAI_API_KEY=sk-from-dotenv\n", encoding="utf-8")
        try:
            assert call("/api/key", name="openai", value=openai)[1]["keys_saved"] == {"claude": True, "openai": True}
            got = call("/api/key/delete", name="openai")[1]
            assert got["keys"]["openai"] and got["keys_saved"] == {"claude": True, "openai": False} and os.environ["OPENAI_API_KEY"] == "sk-from-dotenv", got
        finally:
            env_file.unlink()
        os.environ["OPENAI_API_KEY"] = "sk-outside"  # 밖(환경 변수)에서 준 키는 파일에 없으니 지우지 않는다
        assert call("/api/accounts")[1]["keys"]["openai"] and os.environ["OPENAI_API_KEY"] == "sk-outside"
        assert call("/api/key/delete", name="claude")[1]["keys"] == {"claude": False, "openai": True} and not server.read_json(server.KEY_FILE, {})


def key_check_flow() -> None:
    """키 확인(가짜 응답과 루프백 서버, 외부 네트워크 없음): 공식 주소에 모델 목록 조회 한 번(10초), 결과 여섯. 리다이렉트는 따라가지 않는다. 키 값은 결과·오류 글에 없다."""
    import io
    import urllib.error
    from app.llm import keycheck

    class Reply:  # urlopen이 주는 응답
        def __init__(self, status):
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    seen = []

    def opener(result):
        def open_(request, timeout):
            seen.append((request.full_url, request.get_method(), {k.lower(): v for k, v in request.header_items()}, timeout))
            if isinstance(result, BaseException):
                raise result
            return Reply(result)
        return open_

    http = lambda code: urllib.error.HTTPError("https://example.invalid", code, "x", {}, io.BytesIO(b""))
    secret = "sk-ant-api03-" + "q" * 20
    for result, want in ((200, "ok"), (http(401), "invalid"), (http(403), "denied"), (http(429), "limited"), (http(500), "server"), (http(529), "server"), (http(404), "offline"), (http(302), "offline"),
                         (urllib.error.URLError(f"연결하지 못함 {secret}"), "offline"), (TimeoutError(secret), "offline"), (Reply(302).status, "offline")):
        assert keycheck.check("claude", secret, opener=opener(result)) == want, (result, want)
    seen.clear()
    keycheck.check("claude", secret, opener=opener(200))
    keycheck.check("openai", "sk-proj-" + "r" * 20, opener=opener(200))
    assert [(url, method, timeout) for url, method, _, timeout in seen] == [("https://api.anthropic.com/v1/models?limit=1000", "GET", 10.0), ("https://api.openai.com/v1/models", "GET", 10.0)], seen  # 공식 주소로만, 한 번씩
    assert seen[0][2]["x-api-key"] == secret and seen[0][2]["anthropic-version"] and seen[1][2]["authorization"] == "Bearer sk-proj-" + "r" * 20
    try:
        keycheck.request_for("other", "x")
        raise AssertionError("모르는 공급자는 거절해야 한다")
    except ValueError:
        pass

    # 리다이렉트는 따라가지 않는다: 첫 주소가 302로 다른 호스트를 가리켜도 그 호스트는 키 헤더를 받지 않는다(루프백 서버 둘)
    import http.server
    import threading

    got = []

    class Second(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.append(dict(self.headers))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *args):
            pass

    second = http.server.HTTPServer(("127.0.0.1", 0), Second)

    class First(Second):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{second.server_port}/")
            self.end_headers()

    first = http.server.HTTPServer(("127.0.0.1", 0), First)
    for one in (first, second):
        threading.Thread(target=one.serve_forever, daemon=True).start()

    def to_first(request, timeout):  # 공식 주소 대신 첫 루프백 서버로 보내되, 헤더와 기본 opener(리다이렉트를 따르지 않는 것)는 그대로 쓴다
        return keycheck.OPENER.open(urllib.request.Request(f"http://127.0.0.1:{first.server_port}/", headers=dict(request.header_items())), timeout=timeout)

    def drained(handler):  # 본문을 다 읽고 답한다(읽지 않고 닫으면 Windows가 연결을 리셋해 리다이렉트 대신 연결 오류가 난다)
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            handler(self)
        return do_POST

    Second.do_POST = drained(Second.do_GET)
    First.do_POST = drained(First.do_GET)
    from app.llm import wire
    from app.llm.errors import LlmFailed
    from app.llm.openai.oauth import chat as oauth_chat, token as oauth_token

    def refused(send) -> Exception | None:
        try:
            send()
        except Exception as exc:  # 리다이렉트는 실패로 끝난다(따라가지 않는다)
            return exc
        return None

    try:
        assert keycheck.check("claude", secret, opener=to_first) == "offline" and keycheck.check("openai", "sk-proj-" + "r" * 20, opener=to_first) == "offline"
        here = f"http://127.0.0.1:{first.server_port}/"
        assert isinstance(refused(lambda: wire.post_json(here, {"x-api-key": secret}, {"model": "m"}, timeout=5)), LlmFailed)  # 모델 요청(API 키 연결은 모두 이 길)
        assert isinstance(refused(lambda: oauth_chat.post_sse(here, {"Authorization": "Bearer " + secret}, {"model": "m"})), LlmFailed)  # ChatGPT 요청
        with patch.object(oauth_token, "TOKEN_URL", here):
            assert isinstance(refused(lambda: oauth_token._token({"refresh_token": secret})), oauth_token.Refused)  # 토큰 갱신
        assert got == [], got  # 두 번째 호스트에는 요청도 헤더도 가지 않았다
    finally:
        for one in (first, second):
            one.shutdown()
            one.server_close()

    calls = []

    def fake(result):
        def check(provider, key, **kw):
            calls.append((provider, key))
            return result
        return check

    def put(result, **more):
        with patch.object(server.keycheck, "check", fake(result)):
            return call("/api/key", name="claude", value=f"  {secret}  ", **more)[1]

    def refused(result, **more):
        try:
            put(result, **more)
        except server.Refuse as exc:
            return exc
        raise AssertionError(f"{result}는 거절해야 한다")

    with patch.dict(os.environ, {}):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        server.KEY_FILE.unlink(missing_ok=True)
        # 401은 저장하지 않고 '그래도 저장'도 없다. 403·5xx·연결 못 함은 저장하지 않되 '그래도 저장'을 연다. 429는 키가 맞으니 저장한다
        for result, status, code in (("invalid", 400, "key_invalid"), ("denied", 409, "key_denied"), ("server", 409, "key_unverified"), ("offline", 409, "key_unverified")):
            exc = refused(result)
            assert (exc.status, exc.code, exc.field) == (status, code, "value") and secret not in str(exc), (result, exc.status, exc.code)  # 글에 키 값이 없다
            assert not os.environ.get("ANTHROPIC_API_KEY") and not server.KEY_FILE.exists(), result  # 쓸 수 없는 키, 확인하지 못한 키는 저장하지 않는다
        assert calls == [("claude", secret)] * 4  # 앞뒤 공백은 뗀 값으로 확인한다
        assert "권한" in str(refused("denied")) and "서버가 답하지 않아" in str(refused("server")) and "인터넷" not in str(refused("server")) and "인터넷" in str(refused("offline"))  # 까닭을 단정하지 않고 맞게 말한다
        assert refused("invalid", force=True).code == "key_invalid"  # 틀린 키는 그래도 저장할 수 없다
        assert refused("offline", force="true").code == "key_unverified"  # 정확히 true일 때만 확인 없이 저장한다
        for result in ("denied", "server", "offline"):
            saved = put(result, force=True)
            assert saved["key_check"] == result and saved["keys"]["claude"] and server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": secret}, result
            server.KEY_FILE.unlink()
            os.environ.pop("ANTHROPIC_API_KEY")
        saved = put("limited")  # 429: 키는 맞다. 물음 없이 저장한다
        assert saved["key_check"] == "limited" and server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": secret}
        server.KEY_FILE.unlink()
        os.environ.pop("ANTHROPIC_API_KEY")
        saved = put("ok")
        assert saved["key_check"] == "ok" and secret not in json.dumps(saved) and server.read_json(server.KEY_FILE, {}) == {"ANTHROPIC_API_KEY": secret}
        server.drop_key("ANTHROPIC_API_KEY")


def key_rows_flow() -> None:
    """공급자별 키 줄: 연결 여부, 끝 4자리(나머지 글자는 응답 어디에도 없다), 마지막 확인과 그 결과. 다시 확인은 서버에 있는 키로 하고, 지우면 줄의 확인 기록도 지운다."""
    secret = "sk-ant-api03-" + "Zq7" * 6 + "wxyz"
    short = "sk-abc"
    seen = []

    def fake(result):
        def check(provider, key, **kw):
            seen.append((provider, key))
            return result
        return check

    with patch.dict(os.environ, {}):
        for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_PROVIDER"):
            os.environ.pop(name, None)
        server.KEY_FILE.unlink(missing_ok=True)
        server.KEY_CHECK_FILE.unlink(missing_ok=True)
        empty = call("/api/accounts")[1]
        assert empty["key_rows"] == {name: {"on": False, "tail": "", "at": "", "result": ""} for name in ("claude", "openai")}, empty["key_rows"]
        with patch.object(server.keycheck, "check", fake("ok")):
            body = call("/api/key", name="claude", value=secret)[1]
        row = body["key_rows"]["claude"]
        assert (row["on"], row["tail"], row["result"]) == (True, "wxyz", "ok") and row["at"] and body["using"] == "claude", row
        assert secret[:-4] not in json.dumps(body, ensure_ascii=False) and secret[:-4] not in server.KEY_CHECK_FILE.read_text(encoding="utf-8")  # 끝 4자리 말고는 응답에도 확인 기록에도 없다
        record = server.KEY_CHECK_FILE.read_text(encoding="utf-8")
        assert secret not in record and server.key_print(secret) in record and server.key_print(secret) != secret  # 기록에는 키가 아니라 지문만 있다
        other = "sk-ant-api03-" + "Nn5" * 6 + "9988"  # 키만 바뀐 경우(.env의 키 B를 두고 화면에서 넣은 키 A를 확인한 뒤 다시 켬): 옛 기록은 지금 키의 것이 아니다
        os.environ["ANTHROPIC_API_KEY"] = other
        changed = call("/api/accounts")[1]["key_rows"]["claude"]
        assert changed == {"on": True, "tail": "9988", "at": "", "result": ""}, changed
        os.environ["ANTHROPIC_API_KEY"] = secret
        assert call("/api/accounts")[1]["key_rows"]["claude"]["result"] == "ok"  # 같은 키로 돌아오면 그 기록이 다시 보인다
        import threading  # 키 넣기와 다시 확인이 겹쳐도 공급자의 기록이 서로 덮이지 않는다
        pool = [threading.Thread(target=server.note_key_check, args=(name, "ok", key)) for _ in range(8) for name, key in (("claude", secret), ("openai", "sk-proj-" + "b" * 20))]
        [t.start() for t in pool]
        [t.join() for t in pool]
        assert sorted(server.read_json(server.KEY_CHECK_FILE, {})) == ["claude", "openai"]
        server.note_key_check("openai", None)
        os.environ["OPENAI_API_KEY"] = short  # 너무 짧은 글은 끝자리도 싣지 않는다
        assert call("/api/accounts")[1]["key_rows"]["openai"] == {"on": True, "tail": "", "at": "", "result": ""}
        del os.environ["OPENAI_API_KEY"]
        for result in ("invalid", "denied", "offline", "ok"):  # 다시 확인: 서버에 있는 키로 한 번, 결과와 시각을 남긴다
            seen.clear()
            with patch.object(server.keycheck, "check", fake(result)):
                got = call("/api/key/check", name="claude")[1]
            assert seen == [("claude", secret)] and got["key_check"] == result and got["key_rows"]["claude"]["result"] == result, (result, seen)
            assert secret[:-4] not in json.dumps(got, ensure_ascii=False)
        for bad in ({"name": "x"}, {"name": ["claude"]}):
            assert refuses("/api/key/check", **bad)
        try:
            call("/api/key/check", name="openai")
            raise AssertionError("넣지 않은 키는 확인하지 못한다")
        except server.Refuse as exc:
            assert (exc.status, exc.code) == (409, "key_missing")
        deleted = call("/api/key/delete", name="claude")[1]
        assert deleted["key_rows"]["claude"] == {"on": False, "tail": "", "at": "", "result": ""} and "claude" not in server.read_json(server.KEY_CHECK_FILE, {})
        os.environ["ANTHROPIC_API_KEY"] = secret  # 밖에서 준 키는 확인 기록이 없다(예전 기록이 남았어도 지금 키의 것이 아니면 보이지 않게 지운 상태)
        assert call("/api/accounts")[1]["key_rows"]["claude"]["result"] == ""


def error_lines() -> None:
    """실행 오류 글에서 고른 한 줄(언어마다)."""
    samples = {
        "Traceback (most recent call last):\n  File \"/w/s.py\", line 2, in solution\n    return 1 / 0\nZeroDivisionError: division by zero": "ZeroDivisionError: division by zero",
        "/w/solution.js:2\n    return x();\n           ^\n\nTypeError: x is not a function\n    at solution (/w/solution.js:2:12)\n    at main (/w/run.js:5:1)\n\nNode.js v24.1.0": "TypeError: x is not a function",
        "Exception in thread \"main\" java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3\n\tat Solution.solution(Solution.java:3)\n\tat FunctionRunner.main(FunctionRunner.java:9)":
            "Exception in thread \"main\" java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3",
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
    # 채점기 안쪽 이름(임시 폴더, 호출 파일)은 가리고 내 코드 파일은 '내 코드'로
    assert server.compile_head("/private/var/folders/x/algoblock-check-a1b2/solution.cpp:3:2: error: x was not declared") == '내 코드:3:2: error: x was not declared'
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
    for text, language, words in ((trace, "python", "딕셔너리에 없는 키"), ('Exception in thread "main" java.lang.NullPointerException', "java", "null인 값"),
                                  ("TypeError: x is not a function\n    at solution (/w/solution.js:2:12)", "javascript", "함수가 아닌 것"),
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


def color_tokens() -> None:
    """화면 색: 라이트는 :root, 다크는 :root[data-scheme="dark"] 한 벌. 부품 규칙에는 색 값을 박지 않는다."""
    import re
    css = (HERE / "app.css").read_text(encoding="utf-8")
    html = (HERE / "index.html").read_text(encoding="utf-8")
    assert "prefers-color-scheme" not in css  # 운영체제 설정은 머리의 스크립트가 읽어 data-scheme에 옮긴다
    dark_open = '\n:root[data-scheme="dark"] {\n'
    assert css.count(dark_open) == 1
    dark = css.split(dark_open)[1].split("\n}")[0]
    light = css.split("\n:root {\n")[1].split("\n}")[0]
    for name in ("--thumb", "--scrim", "--code-gutter", "--code-selection", "--syn-keyword", "--syn-string", "--syn-comment", "--syn-number", "--syn-function", "--syn-type"):
        assert f"{name}:" in light and f"{name}:" in dark, name  # 두 화면이 모두 값을 가진다
    rest = css.split("/* ── 바탕 ── */", 1)[1]
    assert [hit for hit in re.findall(r"#[0-9A-Fa-f]{3,8}\b|rgba?\([^)]*\)", rest) if hit != "rgb(255 255 255 / 0.2)"] == []  # 남긴 것: 강조색 면 위의 흰 칠 둘(위), 고르기 화살표 그림(%23)
    assert "var(--code-gutter)" in rest and "var(--thumb)" in rest and "var(--scrim)" in rest
    assert html.index("applyScheme(") < html.index('href="app.css"')  # 첫 그림 전에 정한다
    assert html.count('name="theme-color"') == 1 and 'data-scheme-pref="system"' in html


def tour_pictures() -> None:
    """사용법 안내: 그림이 글과 같은 상태를 보인다. 보고서 장은 빈 상태 없이 강점·더 공부가 함께 보이고, 연결 장은 지금 연결을 따르며, 장을 넘기면 첫 내용이 바로 보인다."""
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    bundle = (HERE / "tour-demos.js").read_text(encoding="utf-8")
    assert "아직 약한 주제로 보이는 곳이 없어요" not in bundle and "더 공부할 주제" in bundle  # 보고서 그림
    assert "demos.show($(\"tour-live\"), tourAt, { conn })" in js and "Claude API 키" not in bundle  # 연결 그림은 지금 연결을 넘겨 받는다(고정 문구 없음)
    assert ".tour-scene .a1 { animation: tour-in 0.35s var(--ease) both; }" in css  # 첫 내용은 기다리지 않고 나온다
    assert ".mini-head::before" in css and "padding: 28px 56px 0" in css  # 정적 그림의 틀이 움직이는 데모의 창과 같다


def tour_follows_screens() -> None:
    """사용법 안내 1·6장이 새 홈(오늘 할 일)과 설정(AI 연결)을 말한다: 글, 정적 그림, 미리 빌드한 움직이는 그림이 같은 이름을 쓰고, 옛 입구 셋·연결 창 글이 남지 않는다."""
    js, html, bundle = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8"), (HERE / "tour-demos.js").read_text(encoding="utf-8")
    tour = js[js.index("const TOUR = ["):js.index("let tourAt = 0;")]
    first, last = tour.split("\n")[1], tour.split("\n")[6]
    assert "오늘 할 일" in first and "입구가 셋" not in first and "‘내 기록’" not in first  # 1장 글
    assert "‘설정’의 ‘AI 연결’" in last  # 6장 글
    scene0 = html[html.index('data-scene="0"'):html.index('data-scene="1"')]
    assert "오늘 할 일" in scene0 and "내 기록" not in scene0 and '>문제 풀기<' not in scene0  # 1장 정적 그림
    scene5 = html[html.index('data-scene="5"'):][:1200]
    assert "설정 · AI 연결" in scene5 and "이미 내는 요금제로 쓰기" in scene5 and "ChatGPT 요금제 쓰기" not in scene5  # 6장 정적 그림
    assert "설정 · AI 연결" in bundle and "이미 내는 요금제로 쓰기" in bundle and "ChatGPT 요금제 쓰기" not in bundle  # 6장 움직이는 그림(stageshow에서 다시 빌드)
    assert "sourceMappingURL" not in bundle and "/Users/" not in bundle and "kimtaekyu" not in bundle  # 만든 파일에 개인 경로나 소스맵 줄이 없다
    assert '$("tour-conn").textContent = CONN.ready ? "연결됨" : "AI 연결 안 됨"' in js


def home_screen() -> None:
    """시작 화면은 홈(대시보드)이다: 빈 주소와 알 수 없는 주소가 홈으로 가고, '오늘 할 일'과 학습 보고서의 맨 위 단추가 같은 규칙(서버 큐의 첫 문제)을 쓴다. 홈이 오늘 출석을 찍는 /api/problems를 부른다."""
    html, js = (HERE / "index.html").read_text(encoding="utf-8"), (HERE / "app.js").read_text(encoding="utf-8")
    assert 'id="view-home"' in html and 'href="#/home" id="nav-home"' in html and 'id="entries"' not in html
    route = js[js.index("function route()"):js.index("function render()")]
    assert route.index('a === "list"') < route.index("return showHome()") and 'return showList();' not in route.replace('a === "list") return showList();', "")
    home = js[js.index("async function showHome()"):js.index("async function showList()")]
    assert 'api("/api/problems")' in home and "nextOf(d.next)" in home and "nextOf(d.next)" in js[js.index("async function showReport()"):js.index("async function showReport()") + 1500]
    status = js[js.index("function homeStatus(d)"):js.index("async function showList()")]
    assert "rd.solved" in status and "sum.solved - rd.solved" in status and "rd.rule_short" in status and 'role="img"' in status  # 도움 없이·그 밖의 통과를 갈라 보이고 기준을 ⓘ로 편다
    assert "도움 받아 통과" not in js and "그 밖의 통과" in status and js.count("그 밖의 통과") >= 6  # 도움을 쓰지 않은 통과(제출 4번째, 처음부터 뒤 하루 안)도 들어 있어서 '도움 받아'라 부르지 않는다
    assert "weaknesses.find" not in js[js.index("async function showReport()"):js.index("async function showReport()") + 1500]  # 보고서 단추가 약한 주제를 따로 앞세우지 않는다
    # 되풀이한 실수: '틀린 곳 같이 찾기'에서만 쌓이니 소개 글이 그렇게 말하고, 목록이 비어도 카드는 남아 쌓이는 법을 한 줄로 안내한다
    report_js = js[js.index("async function showReport()"):js.index("async function showReport()") + 9000]
    assert "‘틀린 곳 같이 찾기’를 쓰면 되풀이한 실수도 모아 줘요" in js and "제출 기록에서 강한 주제와 더 공부할 주제, 자주 하는 실수" not in js
    assert "d.pitfalls.length ? `<section" not in report_js and "‘틀린 곳 같이 찾기’를 쓰면 쌓여요" in report_js


def settings_screen() -> None:
    """설정은 따로 된 화면(#/settings/<분류>)이다: 예전 연결 창의 칸이 id 그대로 분류 안으로 옮겨졌고, 창과 과정별 모델 대화상자는 없다. 분류는 링크라서 뒤로 가기·키보드가 된다."""
    import re
    html, js = (HERE / "index.html").read_text(encoding="utf-8"), (HERE / "app.js").read_text(encoding="utf-8")
    assert 'id="conn-panel"' not in html and 'id="models"' not in html and "toggleConn" not in js and "openModels" not in js
    view = html[html.index('id="view-settings"'):html.index('id="view-feedback"')]
    parts = re.findall(r'<section id="set-(\w+)" class="set-part"', view)
    assert parts == ["ai", "models", "solve", "look", "update"] and re.findall(r'<a href="#/settings/(\w+)"', view) == parts
    moved = {"ai": ["conn-state", "key-rows", "key-value", "key-save", "key-status", "key-delete-confirm", "chatgpt-login", "chatgpt-state", "conn-note"],
             "models": ["models-body", "models-note"], "solve": ["tools-list", "tools-refresh"], "look": ["scheme-kinds"], "update": ["upd-now", "upd-auto", "upd-check", "upd-note"]}
    for part, ids in moved.items():
        block = view[view.index(f'id="set-{part}"'):]
        block = block[:block.index("</section>")] if part != "ai" else block[:block.index('id="set-models"')]
        assert all(f'id="{one}"' in block for one in ids), (part, [one for one in ids if f'id="{one}"' not in block])
    assert 'id="settings-link"' in html and 'href="#/settings/ai"' in html and "‘설정’의 ‘AI 연결’" in js
    assert 'a === "settings"' in js and "setKeyShown(false)" in js[js.index("function route()"):js.index("function render()")]  # 화면을 떠나면 키를 가린다


def aid_note() -> None:
    """문제 상태의 study.unaided_open: 도움 없이 푼 문제로 셀 수 있는 풀이인 동안만 참이다. 힌트, 통과, 제출 3번, 등록 문제에서는 거짓, '처음부터' 뒤에는 다시 참."""
    from types import SimpleNamespace
    state = lambda: call("/api/state", id=PID, mode="chair", open=True)[1]["problem"]["study"]["unaided_open"]  # noqa: E731
    touched = server.read_json(server.TOUCHED_FILE, {})  # 제출하면 '손댄 문제'가 남는다: 뒤 시험의 '다음 문제'가 달라지지 않게 되돌린다
    with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "aid.db"):
        assert state() is True
        call("/api/hint", id=PID)
        assert state() is False  # 힌트를 쓰면 도움 없이 푼 문제에서 빠진다
        call("/api/reset", id=PID)
        assert state() is True  # 처음부터 뒤에는 새 풀이다
    with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "aid.db"):
        for n in range(2):
            call("/api/submit", id=PID, code=f"def solution(*a):\n    return None  # {n}")
        assert state() is True
        call("/api/submit", id=PID, code="def solution(*a):\n    return None  # 2")
        assert state() is False  # 제출 3번을 넘겼다
    with tempfile.TemporaryDirectory() as folder, patch.object(server, "DB", Path(folder) / "aid.db"):
        assert call("/api/submit", id=PID, code=f"{CODE}\n# 0")[1]["ok"] and state() is False  # 통과했다
    server.write_json(server.TOUCHED_FILE, touched)
    js = (HERE / "app.js").read_text(encoding="utf-8")
    assert js.count("aidNote()") >= 4 and "‘그 밖의 통과’로 남아요" in js and "study.unaided_open" in js  # 고르는 칸, 힌트, 튜터 시작 칸, 결과 칸에서 같은 글, 서버가 준 값으로 거른다
    study = {"reset_at": None, "help_after_reset_at": None, "help_first_at": None, "solution_before_pass": False, "hints_seen": 0}
    assert server.unaided_open(SimpleNamespace(builtin=True), [], study, None, False) and not server.unaided_open(SimpleNamespace(builtin=False), [], study, None, False)  # 등록한 문제는 준비도에 들지 않는다
    assert not server.unaided_open(SimpleNamespace(builtin=True), [], study, "2026-01-01T00:00:00+00:00", False)  # 튜터와 말했다


def ai_marks() -> None:
    """AI를 부르는 단추의 작은 표시와 비용 안내(화면 코드 확인): 표시는 data-ai로 한 곳(CSS)에서 그리고, 설정의 금액은 README의 실측 값과 같다. 사진 단계에 AI 사용을 알린다."""
    import re
    js, css, html = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8")
    assert '[data-ai]::after { content: "AI";' in css
    for name in ("to-feedback", "debug-start", "to-explain", "fb-get"):  # 화면 코드가 그리는 단추. 첫 질문·블록 힌트는 저장 힌트로 답해 모델을 부르지 않는다
        assert re.search(rf'id="{name}" class="[^"]*" data-model data-ai', js), name
    for name in ("send", "fq-send", "debug-send", "fb-again"):
        assert re.search(rf'id="{name}" class="[^"]*" data-model data-ai', html), name
    assert "data-ai" not in re.search(r'<button[^>]*id="submit"[^>]*>', html).group(0) and "data-ai" not in re.search(r'<button[^>]*id="run"[^>]*>', html).group(0)  # 채점·실행은 AI가 아니다
    assert "data-ai" not in re.search(r'id="start"[^>]*>', js).group(0) and "data-ai" not in re.search(r'id="result-tutor-hint"[^>]*>', js).group(0)
    assert "보내면 AI가 읽어요" in html
    assert '$("new-submit").toggleAttribute("data-ai", !EDIT && connected())' in js  # 새로 등록하며 AI가 연결됐을 때만
    readme = (HERE.parent.parent / "README.md").read_text(encoding="utf-8")
    note = re.search(r'<p id="cost-note"[^>]*>(.*?)</p>', html, re.S).group(1)
    for amount in ("0.01달러", "0.014달러", "2026년 11월 16일"):
        assert amount in note and amount in readme, amount  # README와 같은 실측 값
    assert "사진은 ‘다음’을 누르면 글로 읽어 와요. AI가 연결돼 있으면 AI가 읽고(사용량이 들어요)" in html and "PDF와 글 파일은 AI를 쓰지 않아요" in html


def report_terms() -> None:
    """학습 보고서의 낱말 풀이와 할 일 하나(화면 코드 확인): 준비도·기준·출석·실전 신호를 한 줄로 풀고, 다음에 배울 주제의 첫 문제가 ‘이어서 풀기’와 같으면 따로 링크하지 않는다."""
    js = (HERE / "app.js").read_text(encoding="utf-8")
    for text in ("도움(튜터·힌트·해설) 없이 푼 기본 문제가 얼마나 쌓였는지 보는 단계예요.", "준비도 기준 보기(어떤 통과를 도움 없이 푼 것으로 세는지)", "앱을 연 날을 세요.",
                 "실전 신호는 풀이 가이드가 짚어 준 단서예요.", "단계는 주제별로 익힌 정도로 정해져요.", "첫 줄이 위의 ‘이어서 풀기’와 같아요.", "모든 문제의 제출을 합친 수예요."):
        assert text in js, text
    import re
    import shutil
    node = shutil.which("node")
    if not node:
        return print("node가 없어 보고서 분기 시험은 건너뜀")
    source = re.search(r"/\* report-pure:start.*?\*/(.*?)/\* report-pure:end \*/", js, re.S).group(1)
    script = source + """
const t = { id: "a" };
console.log(JSON.stringify([focusTail({ next: { id: "a" } }, t), focusTail({ next: { id: "b" } }, t), focusTail({ next: null }, t), focusTail({ next: { id: "a" } }, null),
  sideNext({ next: { id: "a", title: "A" } }, t), sideNext({ next: { id: "b", title: "B" } }, t), sideNext({ next: null }, t)]));
"""
    same, other, none, no_target, side_same, side_other, side_none = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert "첫 문제는 위의" in same and "끝낸 뒤" in other and none == "" and "끝낸 뒤" in no_target  # 같을 때만 ‘첫 문제는 위’, 다르면 링크 없이 순서만
    assert side_same == "" and side_other == "‘이어서 풀기’를 끝낸 뒤: B" and side_none == ""
    pure = js[js.index("const FAIL_WORD"):js.index("const when = ")] + source
    script = pure + """
const f = (o) => failTip(Object.entries({ failed: 0, runtime_error: 0, timeout: 0, compile_error: 0, ...o }));
console.log(JSON.stringify([f({ failed: 1 }), f({ failed: 3 }), f({ failed: 3, timeout: 1 }), f({ failed: 2, timeout: 2 }),
  nextNote([{ why: "쓰던 문제예요." }]), nextNote([{ why: "이어서 풀기" }]), nextNote([{ why: "도움 없이 다시 풀기('처음부터' 뒤 24시간이 지나 다시 풀면 인정)" }]), nextNote([{ why: "새 주제 시작" }])]));
"""
    one, only, most, tie, cont1, cont2, again, fresh = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert "가장 많아요" not in one and "한 번뿐" in one and "가장 많아요" not in only and "모두 ‘오답’" in only  # 한 종류뿐이면(1건이든 여럿이든) 가장 많다고 하지 않는다
    assert "오답이 가장 많아요." in most and "같은 수" in tie  # 비교할 종류가 둘 이상일 때만
    assert "위의 ‘이어서 풀기’와 같아요" in cont1 and "위의 ‘이어서 풀기’와 같아요" in cont2 and "이어서 풀기" not in again and "이어서 풀기" not in fresh  # 첫 줄이 이어서 풀기일 때만 그 말
    src = (HERE / "server.py").read_text(encoding="utf-8")
    watched = re.search(r"nextNote = \(nexts\) => \(nexts\[0\] && /\^\(([^)]*)\)/", js).group(1).split("|")  # nextNote가 보는 글머리
    assert watched == ["쓰던 문제", "이어서 풀기"] and '"쓰던 문제예요."' in src and '(row["next"], row["name"], "이어서 풀기", row["key"])' in src  # 서버의 두 why 문구가 바뀌면 여기서 깨진다(같이 고칠 것)
    assert '"쓰던 문제예요."'.strip('"').startswith(watched[0]) and "이어서 풀기".startswith(watched[1])
    assert "focusTail(focus, target)" in js and "sideNext(x, target)" in js and 'href="#/p/${esc(focus.next.id)}"' not in js


def early_solution_report() -> None:
    """통과하기 전에 해설을 연 문제는 학습 보고서의 주제 줄(early_problems)과 ‘해설을 먼저 본 문제’ 칸에 보인다(해설 확인 창이 그렇게 알린다)."""
    with server.tutor() as t:
        before = t.store.study(PID)
        t.store.set_study(PID, solution_at=server.now(), solution_before_pass=True)
    try:
        rows = {row["key"]: row for row in call("/api/report")[1]["themes"]}
        mine = rows[FIRST["theme"]]
        assert {"id": PID, "title": FIRST["title"]} in mine["early_problems"] and mine["solution_before_pass"] >= 1, mine
    finally:
        with server.tutor() as t:
            t.store.set_study(PID, solution_at=before["solution_at"], solution_before_pass=before["solution_before_pass"])
    js = (HERE / "app.js").read_text(encoding="utf-8")
    assert "<h2>해설을 먼저 본 문제</h2>" in js and "d.themes.flatMap((t) => t.early_problems || [])" in js
    assert "학습 보고서에 ‘해설을 먼저 봄’으로 남아요" in js  # 알림 문구와 같은 이름으로 보인다


def case_arg_count() -> None:
    """내 문제 넣기의 케이스 입력: 인자 수가 시작 코드(표 머리·적은 인자 이름·첫 줄)와 다르면 그 줄 아래에서 알리고, 입력 안내가 인자 목록 전체를 대괄호로 감싼다고 예와 함께 말한다(화면 코드 확인, 분기는 node로)."""
    import re
    import shutil
    js, html = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8")
    assert "인자 목록 전체를 대괄호로 감싸 적어요. 인자가 둘이면 [1, 2], 배열 하나가 인자면 [[1, 2, 3]]처럼 한 번 더 감싸요." in html and html.count("[[1, 2, 3]]") == 1
    assert "리스트" not in html and "리스트" not in js  # 어느 언어로 푸는 사람에게도 보이는 입력 안내라 파이썬 낱말을 쓰지 않는다
    assert "showCalls();" in js and "argNote(args.length, expectedArgs(row))" in js and ".case-call.warn" in (HERE / "app.css").read_text(encoding="utf-8")
    node = shutil.which("node")
    if not node:
        return print("node가 없어 인자 수 안내 시험은 건너뜀")
    source = re.search(r"/\* case-pure:start.*?\*/(.*?)/\* case-pure:end \*/", js, re.S).group(1)
    script = source + "console.log(JSON.stringify([argNote(2, 2), argNote(4, 2), argNote(3, 1), argNote(1, 2), argNote(5, null)]));"
    same, many, wrap, few, unknown = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert same == "" and unknown == ""  # 맞거나 기준이 없으면 말하지 않는다
    assert "인자가 2개인데 4개로 읽혀요." in many and "[1, 2]처럼" in many and "[[1, 2]]" not in many
    assert "인자가 1개인데 3개로 읽혀요." in wrap and "[[1, 2]]처럼 인자 목록 전체를 대괄호로 한 번 더 감싸요." in wrap and "인자가 2개인데 1개로" in few


def way_info() -> None:
    """푸는 방식 설명: 네 방식이 한 자료에서 나오고, ⓘ는 눌러 펴며(키보드·Esc), 잠긴 방식도 글이 읽히고 ⓘ가 열린다. 브라우저 동작은 화면 확인으로 본다."""
    import re
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    table = js[js.index("const WAY_INFO = {"):js.index("const WAYS = ")]
    for key in ("solo", "chair", "guide", "explain"):
        row = re.search(rf"\b{key}: \{{(.*?)\}},\n", table, re.S).group(1)
        assert all(f"{field}:" in row for field in ("name", "line", "needsAi", "does", "when", "ai", "ready")), key
    assert "START = {\n  chair: [WAY_INFO.chair.name, WAY_INFO.chair.does" in js  # 시작 칸의 글도 같은 자료다
    way = js[js.index("function renderWay()"):js.index("function renderTutor()")]
    assert 'aria-disabled="true"' in way and "disabled" not in way.replace("aria-disabled", "")  # 잠가도 Tab이 닿는다
    assert way.index('card("solo")') < way.index('card("chair")') < way.index('card("guide")')  # 도움이 적은 것부터
    assert 'aria-expanded=' in js and 'S.wayInfo = null' in js and '.way-card[aria-disabled="true"]' in css
    assert ".panes.railed .head-info { position: fixed" in css  # 접힌(150px) 칸에서는 머리의 설명을 칸 밖 겹침 상자로 띄운다
    assert "way-card:disabled" not in css and not re.search(r"\.way-card\[aria-disabled[^}]*opacity", css)  # 잠긴 카드의 글은 흐리지 않는다


def keyboard_gaps() -> None:
    """키보드와 AI 표시의 남은 빈틈(화면 코드 확인, 긴 입력 접기는 node로): Esc 뒤 Shift+Tab, 기다리는 중 단추가 초점을 잃지 않음, 사진 읽기의 AI 표시, 긴 실패 입력 접기."""
    import re
    import shutil
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    assert 'if (e.key === "Shift") return;' in js and js.index('if (e.key === "Shift") return;') < js.index('if (e.key === "Escape") return void (ta._tabOut = true);')  # Shift를 누르는 것이 Esc 표시를 지우지 않는다
    busy = js[js.index("function applyBusy()"):js.index('$("timer").textContent')]
    assert 'el.setAttribute("aria-disabled", "true")' in busy and "el.disabled = false" in busy and "el.disabled = !!S.busy" not in js  # 기다림은 disabled가 아니라 aria-disabled
    assert 'el.getAttribute("aria-disabled") === "true") return e.preventDefault();' in js and '.btn[aria-disabled="true"]' in css
    focus = js[js.index("function focusAfter(el)"):js.index("document.addEventListener(\"focusin\"")]
    assert 'put(next.slice(0, 1)' in focus and '$("status")' in focus and "now !== placed" in focus and 'placed === $("status") && now === placed' in focus and 'id="status"' in (HERE / "index.html").read_text(encoding="utf-8") and 'role="status" aria-live="polite" tabindex="-1"' in (HERE / "index.html").read_text(encoding="utf-8")  # 기다리는 동안은 다시 그려진 같은 단추나 상태 글에, 끝난 뒤 다시 그리기가 떨어뜨려도 한 번 더
    assert '[$("start"), $("say"), $("p-title")] : [$("code"), $("p-title")]).find(focusable)' in js  # 방식 카드를 고른 뒤: 보이는 요소로
    assert 'document.querySelector("dialog[open]")' in js and 'e.key === "Tab" && document.querySelector' in js  # 열린 창에서 Tab은 창 안에서만
    assert '"<span data-ai></span>"' in js[js.index("function renderWay()"):js.index("function renderWay()") + 900]  # 연결돼 있을 때 AI를 쓰는 카드에도 AI 표시
    assert '$("read-files").toggleAttribute("data-ai", connected() && FILES.some((x) => x.image))' in js
    assert 'f.longs.map' in js and "전체 입력 보기" in js and "foldLong(m.text)" in js
    node = shutil.which("node")
    if not node:
        return print("node가 없어 긴 입력 접기 시험은 건너뜀")
    source = re.search(r"/\* long-pure:start.*?\*/(.*?)/\* long-pure:end \*/", js, re.S).group(1)
    pairs = ", ".join(f"[{i}, {i + 1}]" for i in range(160))
    script = source + f"const big = `solution([{pairs}]) 에서 틀려요`; const a = foldLong(big), b = foldLong('입력 `[1, 2]`은 작아요'), c = foldLong('긴 글 `' + 'x'.repeat(100) + '` 끝');" + "console.log(JSON.stringify([a, b, c]));"
    a, b, c = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert len(a["text"]) < 120 and a["longs"] and a["longs"][0].startswith("[[0, 1]") and a["text"].endswith("틀려요")  # 160쌍은 앞만 남기고 전체는 따로
    assert b == {"text": "입력 `[1, 2]`은 작아요", "longs": []}  # 짧으면 그대로
    assert c["longs"] == ["`" + "x" * 100 + "`"] and c["text"].startswith("긴 글 `xxxx") and c["text"].endswith("` 끝")


def settings_items() -> None:
    """설정의 기본 언어: /api/prefs가 language를 받아 적고(모르는 언어는 거절), 다른 설정을 지우지 않으며, 다음에 처음 여는 문제의 언어가 된다. 모델 설정은 세 묶음으로 보이고 사용량 글에 숫자가 없다."""
    import re
    saved = server.read_json(server.PREFS_FILE, {})
    try:
        server.write_json(server.PREFS_FILE, {**saved, "stages": {"keep": "me"}, "scheme": "dark"})
        assert call("/api/prefs", language="rust")[1]["language"] == "rust" and server.read_json(server.PREFS_FILE, {})["stages"] == {"keep": "me"}
        assert server.read_json(server.PREFS_FILE, {})["scheme"] == "dark" and server.last_language() == "rust"
        assert "고를 수 없는 언어" in refuses("/api/prefs", language="cobol") and server.last_language() == "rust"
        assert refuses("/api/prefs")  # 보낸 것이 없으면 거절
    finally:
        server.write_json(server.PREFS_FILE, saved)
    js = (HERE / "app.js").read_text(encoding="utf-8")
    groups = js[js.index("const THEME_GROUPS = "):js.index("const EFFORT =")]
    assert all(f'"{key}"' in groups for key in server.themes.THEMES) and not re.search(r"\d+\s*(원|달러|\$|토큰)", js[js.index("const THEME_HELP"):js.index("const EFFORT =")])


def new_draft() -> None:
    """내 문제 넣기: 걸음마다 기록을 쌓아 뒤로 가기가 앞 걸음으로 가고, 적던 글은 이 탭의 sessionStorage에만 둔다(서버나 localStorage로 나가지 않는다). 브라우저 동작은 화면 확인으로 본다."""
    js = (HERE / "app.js").read_text(encoding="utf-8")
    assert "history.pushState({ wstep: n }" in js and 'addEventListener("popstate"' in js
    keep = js[js.index("function saveDraft()"):js.index("function restoreDraft()")]
    assert "sessionStorage.setItem(DRAFT" in keep and "localStorage" not in keep and "api(" not in keep and "fetch(" not in keep
    assert js.count("sessionStorage.removeItem(DRAFT)") >= 2 and "restoreDraft();" in js  # 비우면 지우고, 처음 열 때 되살린다


def menu_and_title_note() -> None:
    """더 보기 메뉴와 내 문제 넣기의 제목 안내(화면 코드 확인): 닫힌 메뉴는 클릭을 받지 않고 Tab으로 나가면 닫히며, 제목 칸 안내는 실제로 채웠을 때만 '첫 줄에서 채웠어요'라고 한다."""
    js, css, html = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8")
    assert ".more:not([open]) > .more-menu { display: none; }" in css
    assert '$("more").addEventListener("focusout"' in js and "!$(\"more\").contains(e.relatedTarget)" in js
    assert "function titleNote()" in js and js.count("titleNote();") >= 2 and "제목을 찾지 못했어요. 문제 이름을 직접 적어 주세요." in js
    assert '<small id="new-title-note" class="hint">글의 첫 줄에서 채웠어요' not in html  # 처음 글에는 채웠다고 말하지 않는다


def pane_widths() -> None:
    """칸 너비: /api/prefs로 세 칸의 몫을 적고, 어긋난 값은 거절한다. 없으면(null) 기본 배치. 다른 설정은 지우지 않는다."""
    import re
    html = (HERE / "index.html").read_text(encoding="utf-8")
    assert re.search(r'id="pane-problem".*?id="sep-problem" role="separator".*?id="pane-code".*?id="sep-tutor" role="separator".*?id="pane-tutor"', html, re.S)  # 칸 사이마다 손잡이(DOM 차례가 Tab 차례)
    saved = server.read_json(server.PREFS_FILE, {})
    server.write_json(server.PREFS_FILE, {**saved, "language": "javascript", "stages": {"keep": "me"}})  # 다른 설정이 같이 남는지 보려고 심는다
    try:
        assert call("/api/accounts")[1]["panes"] is None  # 고르지 않았으면 기본 배치
        for bad in ({}, {"panes": []}, {"panes": [30, 30]}, {"panes": [26, 38, 36, 0]}, {"panes": [4, 50, 46]}, {"panes": [26, 91, -17]}, {"panes": [20, 30, 30]}, {"panes": [40, 40, 40]},
                    {"panes": ["26", "38", "36"]}, {"panes": [True, 50, 49]}, {"panes": [None, 50, 50]}, {"panes": "26,38,36"}, {"panes": {"a": 1}}, {"panes": float("nan")}, {"panes": [float("nan"), 50, 50]}, {"panes": 100}):
            assert "칸 너비" in refuses("/api/prefs", **bad), bad
        assert "panes" not in server.read_json(server.PREFS_FILE, {})  # 거절한 값은 적히지 않는다
        got = call("/api/prefs", panes=[26.1, 38.3, 35.6])[1]
        assert got["panes"] == [26.1, 38.3, 35.6] and server.read_json(server.PREFS_FILE, {})["panes"] == [26.1, 38.3, 35.6] and call("/api/accounts")[1]["panes"] == [26.1, 38.3, 35.6]
        assert call("/api/prefs", panes=[26, 38, 36])[1]["panes"] == [26.0, 38.0, 36.0]  # 정수도 받는다
        assert call("/api/prefs", panes=[25.834, 37.751, 36.42])[1]["panes"] == [25.83, 37.75, 36.42]  # 소수 둘째 자리로 적는다
        assert call("/api/prefs", panes=[5, 90, 5])[1]["panes"] == [5.0, 90.0, 5.0] and call("/api/prefs", panes=[33.33, 33.33, 33.34])[1]["panes"] == [33.33, 33.33, 33.34]  # 끝값과 합 100
        server.write_json(server.PREFS_FILE, {**server.read_json(server.PREFS_FILE, {}), "panes": [1, 2]})  # 손으로 고친 이상한 값은 기본으로 본다
        assert call("/api/accounts")[1]["panes"] is None
        call("/api/prefs", panes=[26.1, 38.3, 35.6])
        assert call("/api/prefs", panes=None)[1]["panes"] is None  # null은 기본으로 돌린다
        both = call("/api/prefs", scheme="dark", panes=[26.1, 38.3, 35.6])[1]  # 둘을 한 번에 보내도 되고, 하나만 보내면 다른 하나는 그대로다
        assert both["scheme"] == "dark" and both["panes"] == [26.1, 38.3, 35.6]
        assert call("/api/prefs", panes=None)[1]["scheme"] == "dark" and call("/api/prefs", scheme="light")[1]["panes"] is None
        call("/api/prefs", panes=[26.1, 38.3, 35.6])
        assert call("/api/prefs", scheme="system")[1]["panes"] == [26.1, 38.3, 35.6] and "scheme" not in server.read_json(server.PREFS_FILE, {})
        assert "칸 너비" in refuses("/api/prefs", scheme="dark", panes=[1, 2])  # 하나가 어긋나면 다른 하나도 적지 않는다
        assert server.read_json(server.PREFS_FILE, {}).get("scheme") is None
        call("/api/prefs", panes=None)
        kept = server.read_json(server.PREFS_FILE, {})
        assert "panes" not in kept and kept["language"] == "javascript" and kept["stages"] == {"keep": "me"}  # 다른 설정은 그대로
    finally:
        server.write_json(server.PREFS_FILE, saved)


def scheme_setting() -> None:
    """화면 색: /api/prefs로 저장하고, 서버가 첫 HTML에 저장한 값을 실어 첫 그림 전에 맞춘다."""
    import threading
    from http.client import HTTPConnection

    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    def first_page() -> str:
        conn = HTTPConnection("127.0.0.1", httpd.server_port, timeout=60)
        conn.request("GET", "/")
        page = conn.getresponse().read().decode("utf-8")
        conn.close()
        return page

    assert [f'name="scheme" value="{value}"' in first_page() for value in ("system", "light", "dark")] == [True] * 3  # 설정 창의 라디오 셋
    saved = server.read_json(server.PREFS_FILE, {})
    server.write_json(server.PREFS_FILE, {**saved, "language": "javascript", "stages": {"keep": "me"}})  # 다른 설정이 같이 남는지 보려고 심는다
    try:
        assert call("/api/accounts")[1]["scheme"] == "system" and 'data-scheme-pref="system"' in first_page()  # 고르지 않았으면 운영체제를 따른다
        for bad in ({}, {"scheme": "sepia"}, {"scheme": ""}, {"scheme": None}, {"scheme": ["dark"]}, {"scheme": 1}):
            assert "화면 색" in refuses("/api/prefs", **bad), bad
        assert "scheme" not in server.read_json(server.PREFS_FILE, {})  # 거절한 값은 적히지 않는다
        for scheme in ("dark", "light"):
            assert call("/api/prefs", scheme=scheme)[1]["scheme"] == scheme
            assert server.read_json(server.PREFS_FILE, {})["scheme"] == scheme and call("/api/accounts")[1]["scheme"] == scheme
            page = first_page()
            assert f'<html lang="ko" data-scheme-pref="{scheme}">' in page
            assert 'data-scheme-pref="system"' in (HERE / "index.html").read_text(encoding="utf-8")  # 파일은 그대로, 내보낼 때만 바꾼다
            assert page.index("applyScheme(") < page.index('href="app.css"')  # 적용하는 스크립트가 스타일시트보다 앞이다
        server.write_json(server.PREFS_FILE, {**server.read_json(server.PREFS_FILE, {}), "scheme": "<x>"})  # 손으로 고친 이상한 값은 system으로 본다
        assert call("/api/accounts")[1]["scheme"] == "system" and 'data-scheme-pref="system"' in first_page()
        call("/api/prefs", scheme="dark")
        assert call("/api/prefs", scheme="system")[1]["scheme"] == "system"
        kept = server.read_json(server.PREFS_FILE, {})
        assert "scheme" not in kept and kept["language"] == "javascript" and kept["stages"] == {"keep": "me"}  # system은 키를 지우고 다른 설정은 그대로
    finally:
        server.write_json(server.PREFS_FILE, saved)
        httpd.shutdown()
        httpd.server_close()


def window_background() -> None:
    """창 바탕색: 고른 색을 따르고, 시스템 설정대로일 때 운영체제를 읽지 못하면 밝은 바탕으로 연다."""
    import types
    from unittest.mock import MagicMock

    sys.modules.setdefault("webview", types.ModuleType("webview"))  # pywebview 없이 함수만 부른다
    import window

    saved = server.read_json(server.PREFS_FILE, {})
    out = lambda text: SimpleNamespace(stdout=text)  # noqa: E731
    try:
        with patch.object(window.sys, "platform", "darwin"):
            with patch.object(window.subprocess, "run", return_value=out("Dark\n")):
                assert window.os_dark() is True
            with patch.object(window.subprocess, "run", return_value=out("")):  # 라이트 운영체제는 값이 없어 빈 글이 온다
                assert window.os_dark() is False
            with patch.object(window.subprocess, "run", side_effect=OSError("defaults 없음")):  # 읽지 못함: 밝게
                assert window.os_dark() is False
            with patch.object(window.subprocess, "run", side_effect=subprocess.TimeoutExpired("defaults", 3)):
                assert window.os_dark() is False
        with patch.object(window.sys, "platform", "linux"):  # 읽는 길이 없는 운영체제
            assert window.os_dark() is False
        for scheme, dark_os, want in (("dark", False, "#111113"), ("light", True, "#F5F5F7"), ("system", True, "#111113"), ("system", False, "#F5F5F7")):
            server.write_json(server.PREFS_FILE, {**saved, **({} if scheme == "system" else {"scheme": scheme})})
            with patch.object(window, "os_dark", MagicMock(return_value=dark_os)):
                assert window.background() == want, (scheme, dark_os)
        server.write_json(server.PREFS_FILE, {**saved, "scheme": "<x>"})  # 이상한 저장 값은 system으로 본다
        with patch.object(window, "os_dark", MagicMock(return_value=False)):
            assert window.background() == "#F5F5F7"
    finally:
        server.write_json(server.PREFS_FILE, saved)


def pane_fit() -> None:
    """칸 너비 계산(app.js의 paneNext)이 어떤 창 너비·몫·글쇠에서도 서버가 받는 범위(각각 5~90, 합 99~101)의 값만 내는지 본다.
    혼자 풀기에서 남은 몫을 코드와 튜터로 나누는 길과 아주 넓은 창에서 최소 너비에 걸린 길을 모두 지난다."""
    import re
    import shutil
    node = shutil.which("node")
    if not node:
        return print("node가 없어 칸 너비 계산 시험은 건너뜀")
    source = re.search(r"/\* pane-pure:start.*?\*/(.*?)/\* pane-pure:end \*/", (HERE / "app.js").read_text(encoding="utf-8"), re.S).group(1)
    script = source + """
let seed = 7;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const out = [];
const triple = () => { const a = rnd() * 100, b = rnd() * (100 - a); return [a, b, 100 - a - b].sort(() => rnd() - 0.5); }; // 범위 밖 몫도 섞는다(아주 넓은 창에서 보이는 너비로 다시 잡은 값)
for (let n = 0; n < 4000; n++) {
  const left = rnd() < 0.5 ? 0 : 1, railed = left === 0 && rnd() < 0.5, span = 500 + rnd() * 12000, shares = n % 3 ? triple() : [25.83, 37.75, 36.42];
  const right = railed ? [1, 2] : [left + 1];
  const b = { left, right, shares, span, min: left === 0 ? [260, 390] : [rnd() < 0.5 ? 390 : 320, rnd() < 0.5 ? 370 : 300], sum: shares[left] + right.reduce((x, i) => x + shares[i], 0) };
  for (const want of [0, Infinity, -1e9, rnd() * span, b.min[0], span - b.min[1]]) out.push([left, railed, want === Infinity ? 1e12 : want, paneNext(b, want)]);
}
// 혼자 풀기에서 문제 칸을 끝까지: 남은 몫을 나누어도 튜터 몫이 5 아래로 가지 않고, 끈 칸(문제)은 그대로다
const repro = paneNext({ left: 0, right: [1, 2], shares: [10.37, 74.88, 14.75], span: 2000, min: [260, 390], sum: 100 }, 1e12);
console.log(JSON.stringify({ out, repro }));
"""
    got = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert len(got["out"]) == 4000 * 6
    bad = [row for row in got["out"] if not server.panes_ok(row[3])]
    assert not bad, bad[:3]
    assert server.panes_ok(got["repro"]) and got["repro"][0] == 80.5 and got["repro"][2] >= 5, got["repro"]


def math_render() -> None:
    """문제 글의 수식·위첨자(app.js의 rich-pure를 node로): 수식 구간만 수식이 되고, 금액·코드·`a^b`·`max_count`는 그대로이며,
    붙여 넣은 글의 스크립트·이벤트 속성·javascript: 링크는 무력하다. 병적 입력도 200ms 안에 끝난다. 정적 파일 세 목록(화면이 부르는 것, 서버 표, 묶음 명세)도 맞춘다."""
    import re
    import shutil
    node = shutil.which("node")
    if not node:
        return print("node가 없어 수식 렌더 시험은 건너뜀")
    js = (HERE / "app.js").read_text(encoding="utf-8")
    source = re.search(r"/\* rich-pure:start.*?\*/(.*?)/\* rich-pure:end \*/", js, re.S).group(1)
    cases = {
        "sub": "값 $a_i$ 와 $$\\sum_{i=1}^{n} a_i$$ 끝", "paren": "식 \\(x^2+1\\) 이고", "bracket": "식 \\[x^2+1\\] 이고",
        "money": "가격은 $5 입니다", "range": "가격은 $5 ~ $10 입니다", "won": "$5짜리 책과 $7짜리 펜", "open": "비용 $x 는 정해지지 않았다",
        "fence": "앞\n```\na$b^c_d $x$\n```\n뒤", "tick": "변수 `a$b^c_d` 를 쓴다",
        "pow5": "1 <= N <= 10^5", "pow9": "답을 10^9+7 로 나눈다", "xor": "a^b 를 출력한다",
        "snake": "max_count 와 A_i와 B_i 를 쓴다", "ol": "1. 첫째\n2. 둘째\n3. 셋째",
        "broken": "깨진 $\\frac{1$ 식", "href": "$\\href{javascript:alert(1)}{x}$", "img": "<img src=x onerror=alert(1)> 글", "script": "<script>alert(1)</script> 글",
        "link": "[x](javascript:alert(1)) 와 [y](JaVaScRiPt:alert(2))", "plain": "그냥 글입니다. 수식 없음.",
        "big": "가나다 $ " * 8000, "dollars": "$" * 1000 + "\n" + "$a$ " * 300, "long": "x_i " * 12000, "open_br": "\\[ a " * 12000, "open_par": "\\( a " * 12000, "tickmath": "값 $a `b` c$ 끝", "rejcode": "\\$`10^5`$", "rejbold": "$$a `**x**` c$",
    }
    script = "const esc = (t) => String(t ?? '').replace(/[&<>\"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', \"'\": '&#39;' }[c]));\n" + source + """
globalThis.window = globalThis;
const katex = require(%s); globalThis.katex = katex;
const cases = %s, out = {};
for (const [k, text] of Object.entries(cases)) {
  const t = process.hrtime.bigint();
  const html = rich(text, true, false);
  const ms = Number(process.hrtime.bigint() - t) / 1e6;
  const tex = [...html.matchAll(/data-tex="([^"]*)"/g)].map((m) => m[1].replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&"));
  const shown = tex.map((x) => katex.renderToString(x, { throwOnError: false, trust: false }));
  out[k] = { html, ms, tex, shown };
}
console.log(JSON.stringify(out));
""" % (json.dumps(str(HERE / "katex" / "katex.min.js")), json.dumps(cases))
    got = json.loads(subprocess.run([node, "-"], input=script, capture_output=True, text=True, check=True).stdout)  # 큰 입력이라 인자 대신 표준 입력으로(리눅스는 인자 하나에 128KB까지다)
    math = lambda k: len(re.findall(r'class="katex"|data-tex=', got[k]["html"]))  # noqa: E731  (KaTeX 결과나 렌더 자리)
    for k in ("sub", "paren", "bracket"):
        assert math(k) >= 1, (k, got[k]["html"])
    assert math("sub") >= 2, got["sub"]["html"]  # 식 둘(렌더 자리의 글은 원문이어도 된다: 깨지면 그대로 보이게)
    for k, kept in (("money", "$5"), ("range", "$5 ~ $10"), ("won", "$5짜리"), ("open", "$x")):  # 금액과 닫히지 않은 $는 글자 그대로
        assert math(k) == 0 and kept in got[k]["html"], (k, got[k]["html"])
    assert "$7짜리" in got["won"]["html"]
    for k, kept in (("fence", "a$b^c_d $x$"), ("tick", "a$b^c_d")):  # 코드 안은 그대로
        assert math(k) == 0 and kept in got[k]["html"] and "<sup>" not in got[k]["html"] and "<em>" not in got[k]["html"], (k, got[k]["html"])
    assert "<sup>5</sup>" in got["pow5"]["html"] and "10<sup>" in got["pow5"]["html"] and "105" not in got["pow5"]["html"], got["pow5"]["html"]
    assert re.search(r"10<sup>9(\+7)?</sup>(\+7)?", got["pow9"]["html"]), got["pow9"]["html"]
    assert "a^b" in got["xor"]["html"] and "<sup>" not in got["xor"]["html"], got["xor"]["html"]  # XOR일 수 있다
    assert "max_count" in got["snake"]["html"] and "A_i와 B_i" in got["snake"]["html"] and not re.search(r"<(em|i)[ >]", got["snake"]["html"]) and math("snake") == 0, got["snake"]["html"]
    assert "<ol>" in got["ol"]["html"] and got["ol"]["html"].count("<li>") == 3, got["ol"]["html"]
    assert math("plain") == 0 and "<sup>" not in got["plain"]["html"]
    assert "katex-error" not in got["broken"]["html"] and "\\frac{1" in got["broken"]["html"], got["broken"]["html"]  # 깨진 수식은 원문 글(화면에서 KaTeX 결과가 오류 표시면 원문으로 되돌린다)
    for k, row in got.items():  # 어떤 글도 스크립트·이벤트 속성·javascript: 링크를 만들지 않는다(KaTeX 결과 포함)
        every = row["html"] + "".join(row["shown"])
        assert not re.search(r"<(script|img|iframe|object|embed)\b", every, re.I), (k, every[:200])
        assert not re.search(r"<[^>]*\son\w+\s*=", every, re.I), (k, every[:200])
        assert not re.search(r"(href|src)\s*=\s*[\"']?\s*javascript:", every, re.I), (k, every[:200])
    assert "<a " not in got["link"]["html"] or "javascript:" not in got["link"]["html"].lower().split("<a ", 1)[1]
    assert "b" in got["tickmath"]["tex"][0] and "\u0000" not in got["tickmath"]["html"] and "`b`" in got["tickmath"]["tex"][0], got["tickmath"]  # 수식 안의 백틱은 쓴 그대로
    assert "<code>10^5</code>" in got["rejcode"]["html"] and "<sup>" not in got["rejcode"]["html"], got["rejcode"]  # 수식이 아닌 $ 구간 안의 코드는 코드 그대로
    assert "<code>**x**</code>" in got["rejbold"]["html"], got["rejbold"]
    for k in ("big", "dollars", "long", "open_br", "open_par"):  # 병적 입력(50KB, $ 1000개, 닫히지 않은 \\[·\\( 수천 번)
        assert got[k]["ms"] < 200, (k, got[k]["ms"])

    # 정적 파일 세 목록: 화면이 부르는 것, 서버 표, 묶음 명세가 같다. 수식 파일은 수식이 있을 때만 받는다(처음 화면은 부르지 않는다)
    html, css = (HERE / "index.html").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    called = set(re.findall(r'(?:src|href)="([^":#]+\.(?:js|css|svg|woff2))"', html)) | set(re.findall(r"url\(\"?([\w./-]+\.woff2)\"?\)", css))
    served = {path.lstrip("/") for path in server.STATIC}
    assert {"/" + name for name in called} <= set(server.STATIC), called - served
    assert not any("katex" in name for name in called), "수식 파일을 처음 화면에서 부른다"
    assert "/katex/katex.min.js" in js and "/katex/katex.min.css" in js, "app.js가 수식이 있을 때 불러오지 않는다"
    kcss = (HERE / "katex" / "katex.min.css").read_text(encoding="utf-8")
    assert not re.search(r"https?://", kcss), "들여온 CSS가 원격 주소를 담고 있다"
    for ref in re.findall(r"url\(([^)]+)\)", kcss):
        ref = ref.strip("\"'")
        assert ref.endswith(".woff2") and "/katex/" + ref in server.STATIC, ref  # woff2만, 모두 서버 표에 있다
    for name, (file, _) in server.STATIC.items():
        assert (HERE / file).is_file(), name
    on_disk = {f"/katex/{p.relative_to(HERE / 'katex').as_posix()}" for p in (HERE / "katex").rglob("*") if p.is_file() and p.suffix in (".js", ".css", ".woff2")}
    assert on_disk == {p for p in server.STATIC if p.startswith("/katex/")}, on_disk ^ {p for p in server.STATIC if p.startswith("/katex/")}
    spec = (HERE.parent / "packaging" / "algoblock.spec").read_text(encoding="utf-8")
    assert "katex" in spec, "묶음 명세에 수식 파일이 없다"
    for name in {file for file, _ in server.STATIC.values() if not file.startswith("katex/")}:
        assert name in spec, name


def split_fit() -> None:
    """세로 나누기: 계산(app.js의 splitNext, 'split-pure' 구역)이 어떤 높이·글쇠에서도 서버가 받는 몫(15~85)을 내고 두 칸의 최소 높이를 지키는지,
    /api/prefs의 rows 저장·검증, 손잡이 마크업, 단추 이동, 창·낮은 화면 설정을 본다. splitNext({ span, min: [편집기 최소, 결과 최소] }, 결과 높이 px) → 결과 몫(%)."""
    import re
    import shutil
    node = shutil.which("node")
    js, css, html = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8"), (HERE / "index.html").read_text(encoding="utf-8")
    found = re.search(r"/\* split-pure:start.*?\*/(.*?)/\* split-pure:end \*/", js, re.S)
    assert found, "app.js에 split-pure 구역이 있어야 한다"
    if node:
        script = found.group(1) + """
let seed = 11;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const out = [];
for (let n = 0; n < 4000; n++) {
  const span = 200 + rnd() * 2400, min = [60 + rnd() * 200, 40 + rnd() * 160];
  for (const want of [0, 1e12, -1e9, NaN, rnd() * span, min[1], span - min[0]]) out.push([span, min, want, splitNext({ span, min }, want)]);
}
console.log(JSON.stringify(out));
"""
        got = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
        assert len(got) == 4000 * 7
        for span, (top, bottom), want, rows in got:
            assert isinstance(rows, (int, float)) and 15 <= rows <= 85, (span, want, rows)
            if top / span <= 0.85 and bottom / span >= 0.15 and top + bottom <= span:  # 두 최소가 15~85 안에서 함께 지켜질 수 있을 때
                assert (100 - rows) * span / 100 >= top - 0.005 * span - 1e-6 or rows >= 85, (span, top, rows)
                assert rows * span / 100 >= bottom - 0.005 * span - 1e-6 or rows <= 15, (span, bottom, rows)
        for span in (300, 534 - 100, 900, 2000):  # 같은 몫이 창 높이가 바뀌어도 범위 안
            for rows in (15, 50, 85):
                assert 15 <= json.loads(subprocess.run([node, "-e", found.group(1) + f"console.log(JSON.stringify(splitNext({{ span: {span}, min: [80, 60] }}, {span} * {rows} / 100)))"], capture_output=True, text=True, check=True).stdout) <= 85
    else:
        print("node가 없어 세로 계산 시험은 건너뜀")

    # /api/prefs의 rows: 15~85 밖·글자·NaN은 거절하고, 다시 읽으면 같은 값이다. 다른 설정은 그대로
    saved = server.read_json(server.PREFS_FILE, {})
    server.write_json(server.PREFS_FILE, {**saved, "language": "javascript", "stages": {"keep": "me"}})
    try:
        for bad in ({"rows": 14.9}, {"rows": 85.1}, {"rows": 0}, {"rows": -30}, {"rows": 100}, {"rows": "40"}, {"rows": "abc"}, {"rows": True}, {"rows": []}, {"rows": [40]}, {"rows": {"a": 1}}, {"rows": float("nan")}, {"rows": float("inf")}):
            assert "높이" in refuses("/api/prefs", **bad), bad
        assert "rows" not in server.read_json(server.PREFS_FILE, {})  # 거절한 값은 적히지 않는다
        for ok in (15, 85, 40, 33.33):
            assert call("/api/prefs", rows=ok)[1]["rows"] == float(ok) and call("/api/accounts")[1]["rows"] == float(ok) and server.read_json(server.PREFS_FILE, {})["rows"] == float(ok)
        assert call("/api/prefs", rows=40.126)[1]["rows"] == 40.13  # 소수 둘째 자리로 적는다
        server.write_json(server.PREFS_FILE, {**server.read_json(server.PREFS_FILE, {}), "rows": 5})  # 손으로 고친 이상한 값은 기본으로 본다
        assert call("/api/accounts")[1]["rows"] is None
        call("/api/prefs", rows=40)
        assert call("/api/prefs", rows=None)[1]["rows"] is None and "rows" not in server.read_json(server.PREFS_FILE, {})  # null은 기본으로 돌린다
        call("/api/prefs", rows=40)
        assert call("/api/prefs", scheme="dark")[1]["rows"] == 40.0  # 다른 값을 바꿔도 rows는 남는다
        call("/api/prefs", scheme="system", rows=None)
        kept = server.read_json(server.PREFS_FILE, {})
        assert kept["language"] == "javascript" and kept["stages"] == {"keep": "me"}
    finally:
        server.write_json(server.PREFS_FILE, saved)

    # 마크업: 편집기와 결과 사이의 세로 손잡이
    assert re.search(r'id="editor".*?id="sep-result"[^>]*>.*?id="result"', html, re.S)
    tag = re.search(r'<div[^>]*id="sep-result"[^>]*>', html).group(0)
    assert 'role="separator"' in tag and 'aria-orientation="horizontal"' in tag and 'tabindex="0"' in tag and "aria-label=" in tag
    assert not re.search(r"\.result\s*\{[^}]*max-height:\s*40%", css)  # 결과 칸의 높이 상한을 없앤다
    mins = re.search(r"\.editor-panel\s*\{[^}]*min-height:\s*calc\((\d+) \* var\(--code-line\)", css)
    assert mins and int(mins.group(1)) == 4, "편집기 최소는 4줄 기준"
    for key in ("ArrowUp", "ArrowDown", "Home", "End", "Escape", "dblclick", "setPointerCapture"):
        assert key in js, key

    # 실행·제출은 오른쪽(튜터) 칸 머리 바로 아래 같은 묶음이고 Tab 차례가 이어진다. id는 그대로
    tutor = html[html.index('id="pane-tutor"'):]
    head_end = tutor.index("</header>")
    run, submit = tutor.index('id="run"'), tutor.index('id="submit"')
    assert head_end < run < submit and "tabindex" not in tutor[run - 60:submit + 60]
    assert not re.search(r"<(button|input|textarea|select|a)\b", tutor[run + 10:submit].rsplit("<", 1)[0]), "둘 사이에 다른 조작이 끼지 않는다"
    assert tutor.count('id="run"') == 1 and tutor.count('id="submit"') == 1
    group = re.search(r"<(div|span)[^>]*>(?:(?!</\1>).)*?id=\"run\"(?:(?!</\1>).)*?id=\"submit\"", tutor, re.S)
    assert group, "실행·제출은 같은 묶음 안"
    code_pane = html[html.index('id="pane-code"'):html.index('id="sep-tutor"')]
    assert 'id="run"' not in code_pane and 'id="submit"' not in code_pane

    # Windows: 창 최소 크기, 세 칸 분기, 낮은 화면
    window = (HERE / "window.py").read_text(encoding="utf-8")
    width, height = map(int, re.search(r"min_size=\((\d+),\s*(\d+)\)", window).groups())
    assert width <= 1092 and height <= 566, (width, height)
    assert "@media (max-width: 1179px)" not in css and "@media (max-width: 1079px)" in css
    assert "@media (min-width: 1180px)" not in css and "@media (min-width: 1080px)" in css
    assert "@media (max-height: 760px)" in css

    # Tab 안내 줄은 늘 자리를 차지하지 않는다(겹침 표시)
    rule = re.search(r"\.tab-hint\s*\{[^}]*\}", css).group(0)
    assert "position: absolute" in rule


def split_kept() -> None:
    """세로 나누기의 화면 상태(화면 코드 확인): 다른 문제로 넘어가면 결과 칸과 함께 손잡이·'결과 크게 보기'도 숨기고 크게 보기를 끄며,
    저장한 몫을 받아 둔 설정(ACCOUNTS)에 넣어 연결 상태가 바뀌어 다시 그려도 끌어 둔 높이로 남는다. 코드 칸 물음의 자리 설명이 사실과 같다."""
    import re
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    body = lambda head: js[js.index(head):js.index("\n}\n", js.index(head))]  # noqa: E731
    clear = body("function clearProblem(")
    hidden = re.search(r"for \(const id of \[([^\]]*)\]\) \$\(id\)\.hidden = true", clear).group(1)
    assert all(f'"{name}"' in hidden for name in ("result", "sep-result", "result-big")), hidden
    assert "splitBig = false" in clear
    save = body("async function paneSave(")
    assert re.search(r"ACCOUNTS.*panes.*rows", save), save
    assert "if ((a.rows ?? null) !== splitRows) splitSet(" in body("function renderAccounts(")  # 같은 높이면 다시 적지 않아 크게 보기가 꺼지지 않는다
    assert "눌렀던 단추 바로 옆" not in css


def stages_split_verify() -> None:
    """과정 표의 문제 나누기·검증 풀이: 화면 목록에 있고, 급을 바꾸면 그 task의 모델이 바뀐다. 예전 ingest 저장은 다섯 과정으로 옮겨진다."""
    from tutor.llm import themes

    rows = {row["key"]: row for row in call("/api/accounts")[1]["themes"]}
    assert {"split", "verify"} <= set(rows)
    assert (rows["split"]["default_tier"], rows["split"]["default_effort"], rows["verify"]["default_tier"], rows["verify"]["default_effort"]) == ("small", "low", "middle", "low")
    assert themes.pick("plan.brute")[0] == "claude/claude-sonnet-5-5" and themes.pick("ingest.outline")[0] == "claude/claude-haiku-5-5"
    call("/api/theme", theme="verify", tier="small", effort="")
    assert themes.pick("plan.brute")[0] == "claude/claude-haiku-5-5" and themes.pick("plan.solve")[0] == "claude/claude-haiku-5-5"
    call("/api/theme", theme="split", tier="large", effort="high")
    assert themes.pick("ingest.outline") == ("claude/claude-opus-5-5", "high")
    assert server.read_json(server.PREFS_FILE, {})["stages"]["split"] == {"tier": "large", "effort": "high"}
    call("/api/theme", theme="verify", tier="", effort=""), call("/api/theme", theme="split", tier="", effort="")
    assert themes.pick("plan.brute")[0] == "claude/claude-sonnet-5-5" and themes.pick("ingest.outline") == ("claude/claude-haiku-5-5", "low")
    themes.choose(themes.from_old({"ingest": {"model": "claude/claude-opus-5-5", "effort": ""}}))  # 서버를 켤 때 예전 설정을 읽는 길
    assert themes.pick("ingest.outline")[0] == themes.pick("plan.brute")[0] == "claude/claude-opus-5-5"
    themes.choose({})


def stages() -> None:
    """과정별 모델: 급과 추론 정도를 고르면 저장되고 바로 쓰인다. 빈 값은 기본값. 모르는 과정·급·정도는 거절한다.
    예전 설정(테마별 모델 이름, Grok·OpenRouter 키)은 조용히 옮기거나 버린다."""
    from tutor.llm import themes

    rows = {row["key"]: row for row in call("/api/accounts")[1]["themes"]}
    assert list(rows) == ["split", "read", "guide", "verify", "blocks", "talk", "judge", "explain", "feedback", "debug"]
    assert {key: (row["default_tier"], row["default_effort"]) for key, row in rows.items()} == {
        "split": ("small", "low"), "verify": ("middle", "low"), "read": ("middle", "high"), "guide": ("small", "high"), "blocks": ("small", "high"), "talk": ("small", "low"),
        "judge": ("small", "low"), "explain": ("small", "medium"), "feedback": ("small", "medium"), "debug": ("small", "medium")}
    assert (rows["read"]["model"], rows["read"]["model_label"], rows["guide"]["model_label"]) == ("claude/claude-sonnet-5-5", "Sonnet 5.5", "Haiku 5.5")
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
    assert [rows[key]["model_label"] for key in ("split", "read", "guide", "verify", "blocks", "talk", "judge")] == ["Opus 5.5"] * 5 + ["Haiku 5.5"] * 2 and rows["talk"]["effort"] == "high"
    call("/api/theme", theme="judge", tier="", effort="")
    prefs = server.read_json(server.PREFS_FILE, {})
    assert "themes" not in prefs and prefs["stages"]["read"] == {"tier": "large", "effort": ""}
    for key in ("split", "read", "guide", "verify", "blocks", "talk"):
        call("/api/theme", theme=key, tier="", effort="")
    assert all(row["tier"] == row["default_tier"] and row["effort"] == row["default_effort"] for row in call("/api/accounts")[1]["themes"])

    # keys.json의 값이 글이 아니면 그 항목만 건너뛰고, 걷어 낸 공급자의 키(Grok·OpenRouter)는 읽지 않는다
    server.write_json(server.KEY_FILE, {"OPENAI_API_KEY": 123, "XAI_API_KEY": "xai-test", "OPENROUTER_API_KEY": "or-test"})
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
            assert len(asked) == 2 and {row["key"]: row["model_label"] for row in body["themes"]}["read"] == "Sonnet 5.6", asked
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
        "all", "예시와 자동 테스트 모두 통과", len(hidden), 1, 2, ["small"]), row
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
    # 글이 바뀌어 ready.json의 출처 값이 맞지 않으면 모델 없이는 가이드를 못 만든다: 그 문제와 까닭을 알리고 0이 아닌 코드로 끝난다
    import shutil
    root = TMP / "stale_root"
    shutil.copytree(HERE / "problems" / "hash" / "1_popular_shelf", root / "hash" / "1_popular_shelf")
    folder = root / "hash" / "1_popular_shelf"
    changed = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
    changed["statement"] += " 입력은 항상 올바릅니다."
    (folder / "problem.json").write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    stale = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(HERE)!r}); import make_builtin as m; from pathlib import Path; m.ROOT = Path({str(root)!r}); "
                            f"sys.exit(m.build(['--no-model', '--no-check', '--no-langs', '--only', 'hash/1_popular_shelf', '--out', {str(TMP / 'stale.json')!r}]))"], capture_output=True, text=True)
    assert stale.returncode == 1 and "hash/1_popular_shelf" in stale.stderr and "출처 값" in stale.stderr, (stale.returncode, stale.stderr)
    (folder / "ready.json").unlink()  # 키 없이 넣은 새 문제처럼 ready.json이 아예 없으면 알리기만 하고 실패로 끝나지 않는다
    fresh = subprocess.run(stale.args, capture_output=True, text=True)
    assert fresh.returncode == 0 and "알림 hash/1_popular_shelf" in fresh.stderr and "실패" not in fresh.stderr, (fresh.returncode, fresh.stderr)


def neutral_notes() -> None:
    """기본 문제 해설(단서의 뜻·익힌 것·흔한 실수·사다리)은 언어마다 갈리지 않으니 한 언어에만 있는 낱말(KeyError, 딕셔너리, heapq 등)이 없어야 한다."""
    import problemkit
    found = [f"{row['id']}: {line}" for row in ROWS for line in problemkit.language_bound(row)]
    assert not found, found
    for saved in sorted((HERE / "problems").glob("*/*/ready.json")):  # 풀이 가이드·블록 힌트도 같다(FIRST의 ready는 아래에서 손으로 바뀌므로 파일을 읽는다)
        found += [f"{saved.parent.name}: {line}" for line in problemkit.ready_bound(json.loads(saved.read_text(encoding="utf-8"))["ready"])]
        found += [f"{saved.parent.name}: {line}" for line in problemkit.guide_names(problemkit.load(saved.parent), json.loads(saved.read_text(encoding="utf-8"))["ready"])]
    assert not found, found
    for word in ("steps 딕셔너리에 담는다", "빈 리스트를 만든다", "mid // 2로 나눈다", "heapq에서 꺼낸다"):
        assert problemkit.ready_bound({"solution": {"steps": [word], "code": "d = {}"}, "plan": {"blocks": [{"hints": [], "reference": "x // 2"}]}}), word
        assert problemkit.ready_bound({"plan": {"blocks": [{"hints": [word]}]}}), word
    assert not problemkit.ready_bound({"solution": {"code": "x = dict()  # 딕셔너리"}, "plan": {"blocks": [{"reference": "a // b"}]}})  # 코드 칸은 보지 않는다
    names = {"statement": "solution 함수. best_size를 구한다", "limits": [], "params": [{"name": "left_over"}], "files": {f"solution.{problemkit.EXT[lang]}": "best_size" for lang in problemkit.GUIDE_LANGS}}
    assert not problemkit.guide_names(names, {"solution": {"steps": ["best_size와 left_over를 본다"]}})  # 다섯 언어에 다 있는 이름·문제 글의 이름은 통과
    assert not problemkit.guide_names({**names, "files": {}}, {"solution": {"steps": ["left_over와 best_size를 본다"]}})  # 문제 글에 있으면 풀이가 없어도 통과
    assert len(problemkit.guide_names({**names, "files": {**names["files"], "solution.java": "bestSize"}, "statement": "x"}, {"solution": {"clues": ["best_size를 쓴다"]}})) == 1  # 한 언어에 없으면 실패
    assert len(problemkit.guide_names(names, {"solution": {"approach": "result가 None이면 True로 둔다"}})) == 2  # 파이썬 전용 값
    bad = {"learn": "x", "pattern": "x", "ladder": "x", "pitfalls": ["count[k] += 1에서 KeyError가 난다"], "signals": [{"means": "딕셔너리에 넣는다"}]}
    assert len(problemkit.language_bound(bad)) == 2  # 걸러야 할 글은 실제로 걸린다
    for word in ("KeyError가 난다", "heapq에서 꺼낸다", "dict로 센다", "int에 담는다", "IndexError가 난다", "long으로 더한다"):  # 한글 조사가 붙은 낱말도 걸린다
        assert problemkit.language_bound({**bad, "pitfalls": [word], "signals": [{"means": "x"}]}), word


def lang_traps() -> None:
    """언어 함정(채점기 없이 보는 것과 Python 하나만 돌리는 것): 저장소의 목록과 증명 파일이 검사를 통과하고, 묶음은 실을 언어의 함정만 싣는다.
    걸러야 할 것(목록에 없는 id, 문제 글에 없는 구절, 쓰지 않는 목록 항목, 바꾼 줄에 함정 표시가 없음, 다른 실수에 이름만 붙임, 너무 많이 넣거나 지움,
    흔한 낱말로만 된 닻, 통과해 버리는 증명 풀이, 본문·케이스가 바뀐 뒤의 lang.json)이 걸린다."""
    import shutil
    import problemkit
    listed = problemkit.traps()
    assert problemkit.trap_list_check() == [] and listed and all(len(rows) <= problemkit.TRAP_MAX for rows in listed.values())
    found = []
    for folder in problemkit.folders([str(HERE / "problems")]):
        problem = problemkit.load(folder)
        found += [f"{folder.name}: {line}" for line in problemkit.lang_check(problem, listed) + problemkit.lang_frozen(problem)]
    assert not found, found
    text = {row["id"]: row for rows in listed.values() for row in rows}
    shipped = 0
    for row in ROWS:  # 시험 묶음은 --no-langs라 Python 함정만 실린다. 글은 목록에서, 떨어진 케이스는 lang.json에서
        path = HERE / "problems" / row["theme"] / row["id"].removeprefix(row["theme"] + "_") / "lang.json"
        frozen = json.loads(path.read_text(encoding="utf-8")).get("python", []) if path.is_file() else []
        mine = (row.get("traps") or {}).get("python", [])
        assert set(row.get("traps") or {}) <= {"python"} and [trap["id"] for trap in mine] == [trap["trap"] for trap in frozen], row["id"]
        assert all(trap["what"] == text[trap["id"]]["what"] and trap["fix"] == text[trap["id"]]["fix"] and (trap.get("fails") or trap.get("varies")) for trap in mine), row["id"]
        # 튜터가 후보를 거르는 이름: 증명 검사와 같게 흔한 낱말과 한 글자는 뺀다
        assert all(trap[key] == [term for term in text[trap["id"]][key] if problemkit.anchor(term)] for trap in mine for key in ("code", "right")), row["id"]
        assert all(isinstance(trap["right_base"], int) and (trap["code"] or trap.get("varies") or trap["right_base"] > 0) for trap in mine), row["id"]  # 정답 풀이에 고친 꼴의 이름이 있다
        assert [trap.get("outs") for trap in mine] == [trap.get("outs") for trap in frozen], row["id"]  # 틀린 답의 돌려준 값도 싣는다
        shipped += len(mine)
    assert shipped >= 5, shipped
    js = (HERE / "app.js").read_text(encoding="utf-8")  # 해설 상자의 꼬리말은 뜻이 드러나는 말이다(내부 참조처럼 '문제 글:'로 쓰지 않는다)
    assert "<small>이 문제에서 걸리는 곳: ${x.at" in js and "<small>문제 글: ${x.at" not in js
    for language, rows in listed.items():  # 결과가 정해지지 않은 동작의 함정은 떨어진 케이스 목록을 얼리지 않는다
        for path in sorted((HERE / "problems").glob("*/*/lang.json")):
            for row in json.loads(path.read_text(encoding="utf-8")).get(language, []):
                assert ("varies" in row) == bool(text[row["trap"]].get("varies")) and ("fails" in row) != ("varies" in row) and "skipped" not in (row.get("fails") or {}).values(), row
                # 틀린 답(failed)의 케이스마다 돌려준 값을 얼린다(같은 케이스에서 다른 값으로 틀리는 다른 버그와 가른다)
                assert set(row.get("outs") or {}) == {cid for cid, status in (row.get("fails") or {}).items() if status == "failed"}, row

    root = TMP / "trap-root"  # 본보기 문제의 사본에서 걸러야 할 것을 하나씩 넣어 본다
    copy = root / "hash" / "1_popular_shelf"
    shutil.copytree(HERE / "problems" / "hash" / "1_popular_shelf", copy)
    good = (copy / "lang_1.py").read_text(encoding="utf-8")
    solution = (copy / "solution.py").read_text(encoding="utf-8")
    body = good.split("\n", 1)[1]

    def check(text: str, name: str = "lang_1.py", folder=copy) -> str:
        (folder / name).write_text(text, encoding="utf-8")
        return "\n".join(problemkit.lang_check(problemkit.load(folder), listed))

    assert check(good) == ""
    assert "목록에 없다" in check("# 언어 함정: python.no_such_trap\n" + body)
    assert "글자 그대로 없다" in check('# 언어 함정: python.missing_key @ "문제 글에 없는 말"\n' + body)
    assert check('# 언어 함정: python.missing_key @ "제목이 같으면 같은 책" "k번째로 빌려지는"\n' + body) == ""  # 구절은 둘까지
    assert "첫 줄이" in check('# 언어 함정: python.missing_key @ "책" "책" "책"\n' + body)
    assert "첫 줄이" in check("// 언어 함정: python.missing_key\n" + body) and "첫 줄이" in check(body)
    assert "정답 풀이와 같다" in check("# 언어 함정: python.missing_key\n" + solution)
    assert "표시가 없다" in check("# 언어 함정: python.missing_key\n" + solution.replace("shelf = []", "shelf = list()"))  # 함정과 상관없는 줄만 바꿨다
    assert "넣은 줄 8개" in check("# 언어 함정: python.missing_key\n" + body.replace("    return shelf", "".join(f"    x{n} = {n}\n" for n in range(7)) + "    return shelf"))
    gutted = "def solution(loans, k):\n    return []\n"  # 거의 다 지우고 남긴 풀이: 지운 줄도 상한이 있다
    assert "지운 줄 7개" in check("# 언어 함정: python.missing_key\n" + gutted)
    for n in (2, 3, 4):
        (copy / f"lang_{n}.py").write_text(good, encoding="utf-8")
    many = check(good)
    assert "4개다(3개까지)" in many and "같은 함정" in many
    for n in (2, 3, 4):
        (copy / f"lang_{n}.py").unlink()
    check(good)
    # 다른 실수(최대 힙)에 넘침 함정의 이름만 붙이면 걸린다: 지운 줄의 right(long long)가 넣은 줄에도 남아 있다
    heap = root / "heap" / "1_snowball_merge"
    shutil.copytree(HERE / "problems" / "heap" / "1_snowball_merge", heap)
    max_heap = (heap / "lang_1.cpp").read_text(encoding="utf-8").split("\n", 1)[1]
    assert check("// 언어 함정: cpp.max_heap\n" + max_heap, "lang_1.cpp", heap) == ""
    assert "표시가 없다" in check("// 언어 함정: cpp.int_overflow\n" + max_heap, "lang_1.cpp", heap)
    # 지운 줄로만 증명하는 함정도 지운 것이 그 함정이어야 한다(음수 번호를 거르는 조건을 남기고 다른 줄을 지웠다)
    dfs = root / "dfs" / "3_folder_size"
    shutil.copytree(HERE / "problems" / "dfs" / "3_folder_size", dfs)
    other = (dfs / "solution.py").read_text(encoding="utf-8").replace("        if size >= limit:\n            count += 1\n", "        count += 1\n")
    assert "표시가 없다" in check("# 언어 함정: python.negative_index\n" + other, "lang_2.py", dfs)
    # 모양 식(shape): 증명 풀이에는 맞고 정답 풀이에는 맞지 않아야 한다(앞으로 도는 size_t 반복은 그 실수가 아니다)
    shutil.copy(HERE / "problems" / "dfs" / "3_folder_size" / "lang_2.py", dfs / "lang_2.py")
    unsigned = (dfs / "lang_1.cpp").read_text(encoding="utf-8")
    assert check(unsigned, "lang_1.cpp", dfs) == ""
    forward = unsigned.replace("for (size_t i = order.size() - 1; i >= 0; i--)", "for (size_t i = 0; i < order.size(); i++)")
    assert forward != unsigned and "모양 식" in check(forward, "lang_1.cpp", dfs)
    check(unsigned, "lang_1.cpp", dfs)
    # 얼린 lang.json에 틀린 답의 돌려준 값이 빠지면 낡은 것이다
    saved_lang = (dfs / "lang.json").read_text(encoding="utf-8")
    assert problemkit.lang_frozen(problemkit.load(dfs)) == []
    stale = json.loads(saved_lang)
    stale["python"] = [{key: value for key, value in row.items() if key != "outs"} for row in stale["python"]]
    (dfs / "lang.json").write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
    assert problemkit.lang_frozen(problemkit.load(dfs))
    (dfs / "lang.json").write_text(saved_lang, encoding="utf-8")
    dfs_cases = problemkit.frozen_cases(problemkit.load(dfs))
    ran = problemkit.lang_run(problemkit.load(dfs), dfs_cases, ["python"], problemkit.saved_limits(problemkit.load(dfs)), listed)[0]["python"]
    assert [row.get("outs") for row in ran] == [row.get("outs") for row in json.loads(saved_lang)["python"]], ran  # 다시 돌려도 같은 값

    # 목록: 쓰는 증명 파일이 없는 항목, 글의 규칙, 흔한 낱말만 있는 닻, 객체가 아닌 항목, 상한
    row = dict(text["python.missing_key"])
    assert problemkit.trap_list_check({"python": [row]}, root) == []
    assert "증명하는 파일" in "\n".join(problemkit.trap_list_check({"python": [row, {**row, "id": "python.unused"}]}, root))
    for bad, words in (({"what": "백틱이 없는 글"}, "백틱"), ({"what": "`KeyError`가 나요. setdefault로"}, "고치는 이름"), ({"fix": "가" * 81}, "81자"),
                       ({"id": "java.missing_key"}, "id는"), ({"right": []}, "대안 이름 목록"), ({"code": "+= 1"}, "이름 목록"), ({"varies": False}, "varies"),
                       ({"code": ["*", "/"], "right": ["for", "int", "get"]}, "닻으로 쓸 이름이 없다"), ({"shape": "("}, "정규식이 아니다"), ({"shape": 3}, "정규식이 아니다")):
        assert words in "\n".join(problemkit.trap_list_check({"python": [{**row, **bad}]}, root)), bad
    assert "칸은" in "\n".join(problemkit.trap_list_check({"python": [row, "글 하나", 3]}, root))  # 객체가 아닌 항목에 죽지 않는다
    assert problemkit.trap_list_check([]) and "13개다" in "\n".join(problemkit.trap_list_check({"python": [row] + [{**row, "id": f"python.more_{n}"} for n in range(12)]}, root))

    # 실행: 증명 풀이가 떨어진 케이스와 상태를 남기고(건너뜀은 빼고), 모두 통과하는 풀이는 걸린다(Python 채점기만 쓴다)
    problem, cases = problemkit.load(copy), problemkit.frozen_cases(problemkit.load(copy))
    rows, more = problemkit.lang_run(problem, cases, ["python"], {}, listed)
    assert more == [] and rows["python"][0]["trap"] == "python.missing_key" and set(rows["python"][0]["fails"].values()) == {"runtime_error"}, (rows, more)
    varied = {"python": [{**row, "varies": True}]}  # 결과가 정해지지 않은 동작의 함정이면 떨어졌다는 것만 남긴다
    assert problemkit.lang_run(problem, cases, ["python"], {}, varied)[0]["python"][0] == {"file": "lang_1.py", "trap": "python.missing_key", "at": ["제목이 같으면 같은 책입니다"], "varies": True}
    (copy / "lang_1.py").write_text("# 언어 함정: python.missing_key\n" + solution, encoding="utf-8")
    rows, more = problemkit.lang_run(problemkit.load(copy), cases, ["python"], {}, listed)
    assert rows == {} and "모든 케이스를 통과한다" in more[0], more
    # lang.json: 이번에 돌리지 않은 언어는 지난 값을 두고, 지운 파일이나 본문·케이스가 바뀐 파일의 행은 뺀다
    (copy / "lang_1.py").write_text(good, encoding="utf-8")
    cases_text = (copy / "cases.json").read_text(encoding="utf-8")
    before = json.loads((copy / "lang.json").read_text(encoding="utf-8"))
    fresh = {"python": [{key: value for key, value in before["python"][0].items() if key != "source"}]}
    problemkit.write_lang(problemkit.load(copy), fresh, ["python"], cases_text)
    assert json.loads((copy / "lang.json").read_text(encoding="utf-8")) == before and problemkit.lang_frozen(problemkit.load(copy)) == []
    (copy / "cases.json").write_text(cases_text.replace('"id": "1"', '"id": "1" ', 1), encoding="utf-8")
    assert problemkit.lang_frozen(problemkit.load(copy))  # 케이스가 바뀌었는데 다시 돌리지 않았다
    (copy / "cases.json").write_text(cases_text, encoding="utf-8")
    (copy / "lang_1.js").write_text((copy / "lang_1.js").read_text(encoding="utf-8") + "\n// 고친 본문\n", encoding="utf-8")
    assert problemkit.lang_frozen(problemkit.load(copy))  # 증명 본문이 바뀌었는데 다시 돌리지 않았다
    problemkit.write_lang(problemkit.load(copy), fresh, ["python"], cases_text)
    assert "javascript" not in json.loads((copy / "lang.json").read_text(encoding="utf-8"))  # 낡은 행은 남기지 않는다(--langs로 다시 돌려야 한다)
    (copy / "lang_1.java").unlink()
    problemkit.write_lang(problemkit.load(copy), fresh, ["python"], cases_text)
    assert "java" not in json.loads((copy / "lang.json").read_text(encoding="utf-8"))


def lang_trap_counterexamples() -> None:
    """실린 함정이 다른 버그를 그 함정으로 내놓지 않는다(채점기 없이). 증명 풀이는 그 함정으로 내놓는다.
    size_t를 앞으로 도는 반복, long long끼리의 곱, 같은 케이스에서 다른 값으로 틀리는 Java 풀이."""
    import problemkit
    from make_builtin import traps_of
    from tutor.debug.rules import trap_candidates, trap_in_code

    def traps(folder: str) -> tuple[dict, dict]:
        problem = problemkit.load(HERE / "problems" / folder)
        files = problem["files"]
        return files, traps_of(problem, {language: files[f"solution.{ext}"] for language, ext in problemkit.EXT.items() if f"solution.{ext}" in files})

    def one(rows: list, trap_id: str) -> dict:
        return next(row for row in rows if row["id"] == trap_id)

    files, folder = traps("dfs/3_folder_size")
    loop = one(folder["cpp"], "cpp.unsigned_loop")
    failed = {"status": "failed", "cases": [{"id": "1", "status": "failed", "got": "0"}]}
    assert trap_candidates([loop], failed, files["lang_1.cpp"]) == [loop]
    forward = files["solution.cpp"].replace("int solution(", "int unused(vector<int> size) {\n    int total = 0;\n    for (size_t i = 0; i < size.size(); i++) total += size[i] - 1;\n    return total;\n}\n\nint solution(")
    assert forward != files["solution.cpp"] and trap_candidates([loop], failed, forward) == [] and trap_candidates([loop], failed, files["solution.cpp"]) == []

    files, charging = traps("binary_search/3_charging")
    multiply = one(charging["cpp"], "cpp.int_multiply")
    assert trap_in_code(multiply, files["lang_2.cpp"]) and not trap_in_code(multiply, files["solution.cpp"])
    wide = files["solution.cpp"].replace("int fastest =", "long long fastest =").replace("(long long)fastest * n", "fastest * n")
    assert wide != files["solution.cpp"] and not trap_in_code(multiply, wide)  # long long끼리의 곱은 넘치지 않는다
    overflow = one(charging["java"], "java.int_overflow")
    cid, out = next(iter(overflow["outs"].items()))
    other = {"status": "failed", "cases": [{"id": cid, "status": "failed", "got": "12345"}]}  # 같은 케이스, 다른 값(다른 버그)
    same = {"status": "failed", "cases": [{"id": cid, "status": "failed", "got": out}]}
    plain = files["solution.java"].replace("long", "var")  # long을 쓰지 않은 풀이(var)
    assert trap_candidates([overflow], other, plain) == [] and trap_candidates([overflow], same, plain) == [overflow]

    # 바깥 *로 늘린 2차원 목록만 그 함정이다(다른 구조로 풀고 다른 버그로 -1을 돌려준 풀이는 아니다)
    files, warehouse = traps("bfs/1_warehouse_robot")
    rows = one(warehouse["python"], "python.shared_rows")
    cid, out = next(iter(rows["outs"].items()))
    same = {"status": "failed", "cases": [{"id": cid, "status": "failed", "got": out}]}
    assert trap_candidates([rows], same, files["lang_1.py"]) == [rows] and trap_candidates([rows], same, files["wrong_3.py"]) == []
    assert trap_candidates([rows], same, "grid = [[]] * n") == [rows] and trap_candidates([rows], same, files["solution.py"]) == []


def problemkit_alone() -> None:
    """설치 묶음에는 튜터 원본 파일이 없다. 서버가 늘 가져오는 problemkit은 가져올 때 튜터를 읽지 않는다(증명 파일을 다룰 때만 가져온다)."""
    folder = TMP / "problemkit-alone"
    folder.mkdir()
    for name in ("problemkit.py", "casegen.py"):
        (folder / name).write_text((HERE / name).read_text(encoding="utf-8"), encoding="utf-8")
    done = subprocess.run([sys.executable, "-B", "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import problemkit; print(problemkit.fits(1, 'int'))", str(folder)],
                          capture_output=True, text=True, cwd=folder)
    assert done.returncode == 0 and done.stdout.strip() == "True", done.stderr[-500:]
    # 증명을 다룰 때는 튜터의 판정 파일을 경로로 읽는다(튜터 묶음과 langgraph 없이). 그 파일이 패키지 안의 다른 모듈을 가져오기 시작하면 이 길이 깨진다
    import problemkit
    from tutor.debug import rules

    text = problemkit.TRAP_RULES.read_text(encoding="utf-8")
    assert not [line for line in text.splitlines() if line.lstrip().startswith(("from .", "import tutor", "from tutor"))], "rules.py는 표준 라이브러리만 가져온다"
    loaded = problemkit.trap_rules()
    assert loaded is not rules and loaded.out_key("찍은 줄\n[1, 2]") == rules.out_key("[1,2]") == "[1,2]"
    shape = {"id": "cpp.unsigned_loop", "shape": r"\bsize_t\s+(\w+)\s*=[^;]*;\s*\1\s*>=\s*0\s*;"}
    assert loaded.shape_in(shape, "for (size_t i = n - 1; i >= 0; i--)") and not loaded.shape_in(shape, "// for (size_t i = n - 1; i >= 0; i--)\nint x;")
    trap = {"id": "python.true_division", "code": [], "right": ["//"], "fails": {"1": "failed"}, "outs": {"1": "2.5"}, "right_base": 1}
    assert loaded.trap_candidates([trap], {"status": "failed", "cases": [{"id": "1", "status": "failed", "got": "2.5"}]}, "a / 2") == [trap]


def solution_traps() -> None:
    """해설은 보이는 정답 코드의 언어에서 증명된 함정을 싣는다(글·고치는 법·문제 글 구절만, 떨어진 케이스는 내보내지 않는다). 화면은 정답 코드 위에 그린다.
    펼친 정답 코드는 사용자가 고른 대로 남는다(다시 그려도, 언어를 바꿔도). 이 분기와 글 꾸미기는 node로 돌려 본다."""
    traps = {"python": [{"id": "python.a", "what": "`a`를 쓰면", "fix": "b", "at": ["제목이 같으면 같은 책입니다"], "fails": {"1": "failed"}}],
             "javascript": [{"id": "javascript.c", "what": "`c`를 쓰면", "fix": "d", "varies": True}]}
    with patch.dict(server.BUILTIN[PID], {"traps": traps}):
        assert call("/api/solution", id=PID, force=True)[1]["traps"] == [{"what": "`a`를 쓰면", "fix": "b", "at": ["제목이 같으면 같은 책입니다"]}]
        assert (server.problem_shape(PID, "python")["traps"], server.problem_shape(PID, "rust")["traps"]) == (traps["python"], [])  # 튜터 엔진은 그 언어의 것만 받는다
        call("/api/language", id=PID, language="javascript")
        try:
            assert call("/api/solution", id=PID, force=True)[1]["traps"] == [{"what": "`c`를 쓰면", "fix": "d"}]
        finally:
            call("/api/language", id=PID, language="python")
    with patch.dict(server.BUILTIN[PID]):
        server.BUILTIN[PID].pop("traps", None)
        assert call("/api/solution", id=PID, force=True)[1]["traps"] == []  # 증명이 없는 문제
        assert server.problem_shape(PID, "python")["traps"] == []
    js, css = (HERE / "app.js").read_text(encoding="utf-8"), (HERE / "app.css").read_text(encoding="utf-8")
    assert '<div class="traps"><h5>이 언어로 풀 때 조심할 것</h5>' in js and js.index('class="traps"') < js.index('<pre class="code"><code>${esc(sol.code') and ".traps {" in css
    change = js[js.index("async function changeLanguage"):js.index("function wantLanguage")]
    assert change.index("const kept = ") < change.index("await work(") and "S.solo.codeOpen = kept.code;" in change  # 기다리는 동안의 다시 그리기 전에 적어 둔다
    assert "codeOpen(S.solo, passed)" in js and "noteCodeToggle(S.solo, summary.parentElement.open)" in js
    import re
    import shutil
    node = shutil.which("node")
    if not node:
        return print("node가 없어 글 꾸미기·정답 코드 펼침 시험은 건너뜀")
    pure = lambda name: re.search(rf"/\* {name}-pure:start.*?\*/(.*?)/\* {name}-pure:end \*/", js, re.S).group(1)  # noqa: E731
    source = js[:js.index("\n", js.index("const esc"))] + pure("inline") + pure("code-open")
    script = source + """
const out = [inline("`a**b**c` 와 **굵게**"), inline("`x` < **y**"), inline("**`k`**")];
let solo = {};                                   // 통과한 문제: 처음에는 접혀 있다
out.push(codeOpen(solo, true));
noteCodeToggle(solo, false);                     // 펼친다
out.push(codeOpen(solo, true));
const kept = solo.codeOpen; solo = { codeOpen: kept };   // 언어를 바꾸면 새 해설 상태로 옮긴다
out.push(codeOpen(solo, true));
noteCodeToggle(solo, true);                      // 접는다
out.push(codeOpen(solo, true), codeOpen({}, false), codeOpen(null, false));
console.log(JSON.stringify(out));
"""
    code, other, wrapped, first, opened, moved, closed, fresh, empty = json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)
    assert code == "<code>a**b**c</code> 와 <strong>굵게</strong>", code  # 백틱 안의 **는 그대로
    assert other == "<code>x</code> &lt; <strong>y</strong>" and wrapped == "<strong><code>k</code></strong>", (other, wrapped)  # 코드를 감싼 굵게는 그대로 된다
    assert (first, opened, moved, closed, fresh, empty) == (False, True, True, False, True, True)  # 접은 뒤에 다시 그려도 펼쳐지지 않는다


def main() -> None:
    neutral_notes()
    lang_traps()
    lang_trap_counterexamples()
    problemkit_alone()
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
        solution_traps()
        compose()
        report()
        pitfalls_repeated()
        labels_follow_language()
        home()
        aid_note()
        own_theme()
        readiness()
        screen_flows()
        debug_pass()
        passed_reopen()
        own_way_flow()
        state_names_by_mode()
        keyboard_focus()
        chair_found()
        guide_spoken()
        same_check_once()
        result_guides()
        language_memory()
        no_tool()
        results()
        tools()
        retired_languages()
        edit_delete()
        checkpoints()
        prep_failed()
        key_flow()
        key_check_flow()
        key_rows_flow()
        prep_unverified()
        two_step_start_is_free()
        two_step_checking_state()
        two_step_keeps_talk()
        two_step_restart()
        two_step_overlap()
        two_step_pending()
        stale_save()
        builtin_prepare()
        own_guide()
        guessed_level()
        kept_languages()
        edit_changes()
        explicit_mode()
        program_mode()
        program_tutor()
        own_starter()
        case_shapes()
        table()
        detect_merge()
        ingest_corpus()
        detect_model()
        tour_pictures()
        tour_follows_screens()
        home_screen()
        settings_screen()
        settings_items()
        keyboard_gaps()
        way_info()
        early_solution_report()
        case_arg_count()
        ai_marks()
        report_terms()
        new_draft()
        menu_and_title_note()
        hidden_cases()
        hint_by_block()
        compile_hints()


        language_switch_state()
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
    assert "Continue with" not in (server.STATIC_DIR / "index.html").read_text(encoding="utf-8")  # 화면 글은 한국어다(ChatGPT 로그인 단추도)

    import test_update  # 업데이트(가짜 네트워크, 임시 폴더의 가짜 앱)
    test_update.run()
    status = call("/api/update", action="status")[1]  # 소스 실행: 확인만 하고 받기·바꾸기는 하지 않는다
    assert status["current"] == server.updater.VERSION and status["frozen"] is False and status["installable"] is False, status
    try:
        call("/api/update", action="download")
        raise AssertionError("받을 새 버전이 없으면 거절한다")
    except server.Refuse as exc:
        assert exc.status == 409
    import test_single  # 앱을 두 번 켰을 때
    test_single.run()
    color_tokens()
    scheme_setting()
    window_background()
    pane_widths()
    pane_fit()
    math_render()
    split_fit()
    split_kept()
    stages()
    stages_split_verify()
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
