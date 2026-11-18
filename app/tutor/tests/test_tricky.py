"""숨은 테스트 만들기의 모델 쪽: 생성기 프롬프트에 함정 입력, 큰 입력을 가리지 못하면 생성기를 한 번만 다시 받는다. 가짜 모델과 가짜 실행기, 모델 0회."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from . import fakes
from .test_tutor import CODE, LINED, SOLVED
from ..llm import FakeLlm, LlmTimeout
from ..main import Tutor
from ..plan import nodes
from ..plan.prompts import maker_messages

BRUTE = {"code": "```python\ndef solution(a, b):\n    return [x for x in a if a.count(x) > b.count(x)][0]\n```"}
MAKER = {"code": "def small():\n    return [[['a'], []]]\ndef edge():\n    return []\ndef tricky():\n    return []\ndef large():\n    return []",
         "bounds": [{"arg": 0, "shortest": 1, "longest": 100000}]}
AGAIN = {**MAKER, "code": MAKER["code"] + "\n# 다시 받은 생성기"}
COUNTS = {"edge": 6, "tricky": 5, "random": 9, "efficiency": 3}
SAME = {"status": "same", "hidden": 20, "efficiency": 3, "counts": COUNTS, "indistinct": False}
BLIND = {**SAME, "indistinct": True}  # 단순 풀이가 큰 입력을 모두 끝냈다


class TrickyNodesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = str(Path(self.dir.name) / "tutor.db")

    def crossed(self, scripts, results):
        seen = {"runs": [], "done": []}

        def run(pid, code, brute, maker, bounds):
            seen["runs"].append(maker)
            return dict(results.pop(0))

        cross = mock.Mock(mode=lambda pid: "function", run=run, done=lambda pid, verdict: seen["done"].append(verdict))
        fake = FakeLlm(scripts)
        tutor = Tutor(self.path, client=fake, check=lambda pid, code: {"status": "passed", "cases": []}, cross=cross)
        self.addCleanup(tutor.close)
        tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
        tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
        return tutor, fake, seen

    def test_generator_prompt_asks_for_tricky_and_never_for_answers(self):
        for mode in ("function", "program"):
            text = "\n".join(message["content"] if isinstance(message["content"], str) else str(message["content"]) for message in maker_messages("정수의 합을 구한다.", mode))
            self.assertIn("tricky()", text)
            self.assertIn("small()", text)  # 기존 함수 요구는 그대로

    def test_distinguishing_big_input_needs_no_extra_generator_call(self):
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], "plan.brute": [BRUTE], "plan.cases": [MAKER], **LINED}, [SAME])
        self.assertEqual(tutor.prepare("p1").status, 200)
        self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.brute", "plan.cases", "plan.draft_blocks"])
        done = seen["done"][0]
        self.assertEqual((done["calls"], done["counts"], done["indistinct"]), (2, COUNTS, False))

    def test_indistinct_big_input_asks_the_middle_tier_for_a_generator_once(self):
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], "plan.brute": [BRUTE], "plan.cases": [MAKER, AGAIN, AGAIN], **LINED}, [BLIND, BLIND, BLIND])
        self.assertEqual(tutor.prepare("p1").status, 200)
        self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.brute", "plan.cases", "plan.cases", "plan.draft_blocks"])  # 한 번뿐
        again = [call for call in fake.calls if call["task"] == "plan.cases"][1]
        self.assertIn("sonnet", again["params"]["model"])  # 가운데 급
        self.assertEqual(seen["runs"][1], AGAIN["code"])  # 다시 받은 생성기로 다시 대조했다
        self.assertEqual(len(seen["runs"]), 2)
        done = seen["done"][0]
        self.assertEqual((done["calls"], done["indistinct"], done["verified"]), (3, True, "all"))  # 끝내 못 가리면 '가리지 못함'으로 남는다

    def test_retry_that_distinguishes_clears_the_mark(self):
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], "plan.brute": [BRUTE], "plan.cases": [MAKER, AGAIN], **LINED}, [BLIND, SAME])
        self.assertEqual(tutor.prepare("p1").status, 200)
        done = seen["done"][0]
        self.assertEqual((done["calls"], done["indistinct"], done["counts"]), (3, False, COUNTS))

    def test_failed_retry_keeps_the_first_result(self):
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], "plan.brute": [BRUTE], "plan.cases": [MAKER, LlmTimeout("시간 초과")], **LINED}, [BLIND])
        self.assertEqual(tutor.prepare("p1").status, 200)
        done = seen["done"][0]
        self.assertEqual((len(seen["runs"]), done["indistinct"], done["verified"]), (1, True, "all"))

    def test_extra_calls_never_pass_the_cap(self):
        differ = {"status": "differ", "input": "[]", "got": "1", "want": "2"}
        other = {**SOLVED, "code": CODE.replace("count = {}", "count = dict()")}
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED, other, other], "plan.brute": [BRUTE], "plan.cases": [MAKER, AGAIN, AGAIN], **LINED},
                                         [differ, differ, BLIND, BLIND, BLIND])
        self.assertEqual(tutor.prepare("p1").status, 200)
        self.assertLessEqual(seen["done"][0]["calls"], nodes.EXTRA_CALLS)
        self.assertEqual(fakes.tasks(fake).count("plan.cases"), 2)  # 다시 받기는 한 번

    def test_retry_is_skipped_when_the_cap_is_used_up(self):
        differ = {"status": "differ", "input": "[]", "got": "1", "want": "2"}
        other = {**SOLVED, "code": CODE.replace("count = {}", "count = dict()")}
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED, other, other], "plan.brute": [BRUTE], "plan.cases": [MAKER, AGAIN], **LINED}, [differ, differ, BLIND])
        with mock.patch.object(nodes, "EXTRA_CALLS", 4):  # 다시 풀기 둘로 4회를 다 썼다
            self.assertEqual(tutor.prepare("p1").status, 200)
        self.assertEqual((fakes.tasks(fake).count("plan.cases"), seen["done"][0]["calls"]), (1, 4))


if __name__ == "__main__":
    unittest.main()
