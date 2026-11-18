"""풀이 준비의 사다리: 정답 풀이가 공개 예시를 못 맞히면 다시 쓸 때 한 급 올리고, 쓴 급을 남기고, 추가 호출은 상한을 지킨다."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from . import fakes
from ..llm import FakeLlm, themes
from ..main import Tutor
from .test_tutor import CODE, LINED, SOLVED

FIXED = {**SOLVED, "code": CODE.replace("count = {}", "count = dict()")}  # 줄 수가 같아 같은 블록 초안으로 나뉜다
BRUTE = {"code": "def solution(a, b):\n    return [x for x in a if a.count(x) > b.count(x)][0]"}
MAKER = {"code": "def small():\n    return []\ndef edge():\n    return []\ndef large():\n    return []", "bounds": [{"arg": 0, "shortest": 1, "longest": 100000}]}
FAILED = {"status": "failed", "cases": [{"id": "1", "kind": "example", "input": "[]", "expected": "1", "got": "2", "status": "failed"}]}
PASSED = {"status": "passed", "cases": []}
DIFFER = {"status": "differ", "input": "[]", "got": "1", "want": "2"}


def series(fake, task="plan.solve"):
    return [next(s for s in ("haiku", "sonnet", "opus") if s in c["params"]["model"]) for c in fake.calls if c["task"] == task]


class TwoStepLadderTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.addCleanup(themes.choose, {})

    def run_prepare(self, reports, results, solves=None):
        """reports: 공개 예시 채점 결과가 차례로, results: 대조 실행기 결과가 차례로. (가짜 모델, 대조 기록)."""
        seen, reports = {"done": []}, list(reports)
        cross = mock.Mock(mode=lambda pid: "function", run=lambda *a: results.pop(0), done=lambda pid, verdict: seen["done"].append(verdict))
        fake = FakeLlm({"plan.solve": solves or [SOLVED, FIXED, FIXED, FIXED, FIXED, FIXED], "plan.brute": [BRUTE], "plan.cases": [MAKER], **LINED})
        tutor = Tutor(str(Path(self.dir.name) / "t.db"), client=fake, check=lambda pid, code: reports.pop(0) if len(reports) > 1 else reports[0], cross=cross)
        try:
            tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
            tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
            self.assertEqual(tutor.prepare("p1").status, 200)
        finally:
            tutor.close()
        return fake, seen

    def test_failed_example_retries_one_tier_up_and_records_it(self):
        fake, seen = self.run_prepare([FAILED, PASSED], [{"status": "same", "hidden": 3, "efficiency": 0}])
        self.assertEqual(series(fake)[:2], ["haiku", "sonnet"])  # 둘째 시도는 한 급 위
        self.assertEqual(seen["done"][0]["tiers"][:2], ["small", "middle"])  # 쓴 급이 남는다
        self.assertEqual(seen["done"][0]["verified"], "all")

    def test_second_failure_goes_to_the_large_tier(self):
        fake, seen = self.run_prepare([FAILED, FAILED, PASSED], [{"status": "same", "hidden": 3, "efficiency": 0}])
        self.assertEqual(series(fake)[:3], ["haiku", "sonnet", "opus"])
        self.assertEqual(seen["done"][0]["tiers"][:3], ["small", "middle", "large"])

    def test_retry_stays_when_the_guide_tier_is_already_middle(self):
        themes.choose({"guide": {"tier": "middle", "effort": ""}})
        fake, seen = self.run_prepare([FAILED, PASSED], [{"status": "same", "hidden": 3, "efficiency": 0}])
        self.assertEqual(series(fake)[:2], ["sonnet", "sonnet"])  # 이미 가운데라 올리지 않는다
        self.assertNotIn("large", seen["done"][0]["tiers"])

    def test_extra_calls_stay_within_the_cap(self):
        """예시 실패 두 번 뒤 통과하고 대조가 계속 달라도 문제 하나의 추가 호출은 상한 안이다."""
        fake, seen = self.run_prepare([FAILED, FAILED, PASSED], [DIFFER, DIFFER, DIFFER])
        self.assertLessEqual(seen["done"][0]["calls"], 5)
        extra = [c for c in fake.calls if c["task"] in ("plan.solve", "plan.brute", "plan.cases")]
        self.assertLessEqual(len(extra), 1 + 5 + 2, [c["task"] for c in fake.calls])  # 처음 풀이 + 대조 상한 + 예시 재시도 둘


class LaterCrossTest(unittest.TestCase):
    """대조 없이 준비하고(서버 준비의 1걸음) 나중에 대조할 때(2걸음): 1걸음이 맡긴 채점 결과와 쓴 급으로 대조 결과를 적는다."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def prepare_then_recheck(self, reports):
        kept, done, path = {}, [], str(Path(self.dir.name) / "t.db")
        check = lambda pid, code: reports.pop(0) if len(reports) > 1 else reports[0]
        later = SimpleNamespace(mode=lambda pid: "function", run=None, later=lambda pid, report, tiers: kept.update(report=report, tiers=tiers))
        first = Tutor(path, client=FakeLlm({"plan.solve": [SOLVED, FIXED, FIXED], **LINED}), check=check, cross=later)
        try:
            first.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
            first.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
            self.assertEqual(first.prepare("p1").status, 200)
            self.assertFalse([c["task"] for c in first.client.calls if c["task"] in ("plan.brute", "plan.cases")])  # 1걸음은 대조하지 않는다
        finally:
            first.close()
        cross = SimpleNamespace(mode=lambda pid: "function", run=lambda *a: self.fail("예시를 통과하지 못한 가이드는 대조를 돌리지 않는다"), done=lambda pid, verdict: done.append(verdict))
        again = Tutor(path, client=FakeLlm({}), check=check, cross=cross)
        try:
            self.assertIsNone(again.recheck("p1", **kept))
        finally:
            again.close()
        return done[0]

    def test_unrun_reason_is_kept(self):
        """도구가 없어 채점하지 못한 가이드: '돌려 볼 케이스가 없어요'가 아니라 도구가 없다는 까닭과 설치 안내가 남는다."""
        verdict = self.prepare_then_recheck([{"status": "toolchain_missing", "cases": []}])
        self.assertIn("도구가 없어요", verdict["why"])
        self.assertIn("설치하면", verdict["why"])
        self.assertEqual((verdict["verified"], verdict["tiers"]), ("none", ["small"]))

    def test_failed_examples_and_tiers_are_kept(self):
        """세 번 다 예시를 못 맞힌 가이드: 맞지 않은 예시가 doubts에 남고, 쓴 급이 처음부터 차례로 남는다."""
        verdict = self.prepare_then_recheck([FAILED])
        self.assertEqual(verdict["doubts"], [{"where": "예시 1", "note": "기대 결과와 풀이가 맞지 않음"}])
        self.assertEqual(verdict["tiers"], ["small", "middle", "large"])


if __name__ == "__main__":
    unittest.main()
