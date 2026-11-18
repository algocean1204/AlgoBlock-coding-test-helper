"""등록한 문제의 숨은 케이스에 종류 꼬리표가 남고 결과 칸에 종류별 수가 보인다(server.cross_run, 실제 채점기, 모델 0회).

실행: cd app && python3.14 -B ui/test_tricky_server.py
계약: cross_run이 붙인 정확성 케이스는 tag('edge'·'tricky'·'random')를 갖고, cross_run 결과와 문제 목록의 check에 counts·indistinct가 있다.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="algoblock-tricky-test-"))
os.environ["ALGOBLOCK_UI_DATA"] = str(TMP / "data")
os.environ["ALGOBLOCK_UI_BUILTIN"] = str(TMP / "builtin.json")
os.environ["ALGOBLOCK_UI_PREPARE"] = "0"
for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_MODEL", "ALGOBLOCK_LLM_PROVIDER"):
    os.environ.pop(name, None)
sys.path[:0] = [str(HERE), str(HERE.parent)]
Path(os.environ["ALGOBLOCK_UI_BUILTIN"]).write_text("[]", encoding="utf-8")

import server  # noqa: E402
from tutor.state import Bound  # noqa: E402

TEXT = "정수 배열 numbers의 모든 원소의 합을 return 하도록 solution 함수를 완성하세요.\n\n제한사항\n- numbers의 길이는 1 이상 100,000 이하입니다.\n- 원소는 -1,000 이상 1,000 이하입니다."
CODE = "def solution(a):\n    total = 0\n    for number in a:\n        total += number\n    return total"
MAKER = ("import random\ndef small():\n    return [[[random.randint(10, 99) for _ in range(random.randint(1, 8))]] for _ in range(21)]\n"
         "def edge():\n    return [[[-1000]], [[1000, 1000, 1000]], [[7]]]\n"
         "def tricky():\n    return [[[0, 0, 0]], [[1000, -1000]], [[-1, -1, -1]], [[5000]]]\n"
         "def large():\n    return [[[random.randint(-1000, 1000) for _ in range(20000)]]]\n")
BOUNDS = [Bound(arg=0, low=-1000, high=1000, shortest=1, longest=100000)]


class TrickyServerTest(unittest.TestCase):
    def test_made_cases_carry_tags_and_the_check_shows_counts(self):
        pid = server.register({"title": "배열의 합", "text": TEXT, "cases": [{"input": "[[1, 2, 3]]", "expected": "6"}]})["id"]
        found = server.cross_run(pid, CODE, "def solution(a):\n    return sum(a)", MAKER, BOUNDS)
        self.assertEqual(found["status"], "same", found)
        made = [case for case in server.PROBLEMS[pid].cases if case.get("made")]
        tags = [case.get("tag") for case in made if case["kind"] == "accuracy"]
        self.assertEqual(tags[:9], ["edge", "tricky", "random"] * 3)
        self.assertEqual({tag: tags.count(tag) for tag in ("edge", "tricky", "random")}, {"edge": 3, "tricky": 3, "random": 14})
        self.assertEqual(found["counts"], {"edge": 3, "tricky": 3, "random": 14, "efficiency": 1})
        self.assertIn("indistinct", found)
        self.assertNotIn("5000", json.dumps([case["input"] for case in made if "input" in case]))  # 제한사항을 어긴 함정 입력은 붙지 않는다
        verdict = {"verified": "all", "calls": 2, "tiers": ["small"], "doubts": [], "why": "", "hidden": found["hidden"], "efficiency": found["efficiency"],
                   "counts": found["counts"], "indistinct": found["indistinct"]}
        server.cross_done(pid, verdict)
        row = next(row for row in server.handle("/api/problems", {})[1]["problems"] if row["id"] == pid)
        self.assertEqual((row["check"]["counts"], row["check"]["indistinct"]), (found["counts"], found["indistinct"]))  # 문제 머리의 요약이 읽는 곳


if __name__ == "__main__":
    unittest.main()
