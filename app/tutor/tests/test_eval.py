"""평가기 시험: 규칙 검사, 모델 평가기 표 세기(근거 검증·다수결), 보정 지표, 캐시 경계 표시."""

import unittest

from ..eval import checks
from ..eval.calibrate import kappa, score
from ..eval.golden import GOLDEN
from ..eval.judge import judge, parse_vote, tally
from ..llm import FakeLlm, use_llm
from . import fakes

PROBLEM = fakes.PROBLEM
HIDDEN = {"name": "이름 세기", "goal": "센다", "checks": ["센다"], "reference": "count[p] = count.get(p, 0) + 1",
          "later_names": ["다시 훑어 찾기"]}


def row(reply, move="open", **extra):
    return {"kind": "turn", "mode": "chair", "status": 200, "reply": reply, "move": move, "hidden": HIDDEN, "problem": PROBLEM, **extra}


class ChecksTest(unittest.TestCase):
    def test_reply_flags(self):
        self.assertEqual(checks.reply_flags(row("이 블록에서 무엇을 기록해 둘까요?"), None), [])
        self.assertIn("참고 코드 유출", checks.reply_flags(row("count[p] = count.get(p, 0) + 1 로 셀까요?"), None))
        self.assertIn("뒤 블록 이름", checks.reply_flags(row("다시 훑어 찾기 전에 무엇을 할까요?"), None))
        self.assertIn("금지 표현", checks.reply_flags(row("좋아요, 다음은 무엇일까요?"), None))
        self.assertIn("질문으로 안 끝남", checks.reply_flags(row("이름을 세세요."), None))
        self.assertIn("문항에 없는 인용", checks.reply_flags(row("'중복은 없다'를 보면 어떨까요?"), None))
        self.assertIn("직전과 같은 말", checks.reply_flags(row("무엇을 셀까요?"), "무엇을 셀까요?"))

    def test_fallback_detected_even_with_lead(self):
        from ..common.talk_rules import FALLBACK, RETRY_LEAD

        self.assertTrue(checks.is_fallback(RETRY_LEAD + FALLBACK["trace"], "trace"))
        self.assertFalse(checks.is_fallback("가장 작은 예로 따라가 볼까요?", "trace"))
        self.assertFalse(checks.is_fallback(FALLBACK["close"], "close"))

    def test_session_metrics(self):
        rows = checks.annotate([
            row("무엇을 셀까요?", event="start", open_count=1, blocks_total=2, seconds=1.0),
            row("무엇을 셀까요?", event="message", user="몰라요", advance=False, open_count=1, blocks_total=2, seconds=3.0),
            row("다음은요?", event="message", user="세요", advance=True, open_count=2, blocks_total=2, seconds=2.0),
            {"kind": "submit", "status": 200, "ok": True},
        ])
        got = checks.session_metrics(rows, [{"input": 10, "cache_read": 90, "cache_write": 0}])
        self.assertEqual((got["repeat"], got["max_stuck"], got["blocks_open"], got["submitted_ok"]), (1, 1, 2, True))
        self.assertEqual(got["cache_hit_rate"], 0.9)
        self.assertEqual(got["latency_p50"], 2.0)


ITEM = {"user": "returned에 있는지만 보면 돼요", "reply": "dict로 이름마다 세면 어떨까요?"}


class JudgeTallyTest(unittest.TestCase):
    def test_fail_needs_verbatim_evidence(self):
        good = {"leak": {"label": "fail", "evidence": "dict로 이름마다 세면", "reason": "기법 노출"}}
        made_up = {"leak": {"label": "fail", "evidence": "딕셔너리를 쓰세요", "reason": "지어낸 인용"}}
        self.assertEqual(tally([good, good, made_up], ITEM)["leak"]["label"], "fail")
        got = tally([made_up, made_up, good], ITEM)["leak"]
        self.assertEqual((got["label"], got["valid"]), ("uncertain", 1))  # 무효 2표 → 과반 없음

    def test_verdict_evidence_comes_from_user(self):
        vote = {"verdict": {"label": "fail", "evidence": "returned에 있는지만", "reason": ""}}
        self.assertEqual(tally([vote] * 3, ITEM)["verdict"]["label"], "fail")
        wrong_place = {"verdict": {"label": "fail", "evidence": "dict로 이름마다", "reason": ""}}
        self.assertEqual(tally([wrong_place] * 3, ITEM)["verdict"]["label"], "uncertain")

    def test_split_votes_are_unstable(self):
        p = {"novice_fit": {"label": "pass"}}
        got = tally([p, p, None], ITEM)["novice_fit"]
        self.assertEqual((got["label"], got["agree"]), ("pass", 1.0))
        f = {"novice_fit": {"label": "fail", "evidence": "dict로", "reason": ""}}
        self.assertEqual(tally([p, f, None], ITEM)["novice_fit"]["label"], "uncertain")

    def test_parse_vote_and_parallel_fake(self):
        self.assertEqual(parse_vote('앞말 {"leak": {"label": "pass"}} 뒷말'), {"leak": {"label": "pass"}})
        self.assertIsNone(parse_vote("JSON 아님"))
        vote = '{"leak": {"label": "pass"}, "responsive": {"label": "pass"}}'
        fake = FakeLlm({"eval.judge": [vote, vote, "깨진 출력"]})
        with use_llm(fake):
            got = judge(GOLDEN[0]["item"], k=3)
        self.assertEqual(len(fake.calls), 3)  # 일꾼 스레드에서도 끼운 모델을 쓴다
        self.assertEqual(got["leak"]["label"], "pass")


class CalibrateTest(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(kappa([("pass", "pass"), ("fail", "fail")]), 1.0)
        self.assertIsNone(kappa([("pass", "pass")] * 3))
        self.assertLess(kappa([("pass", "fail"), ("fail", "pass")]), 0)

    def test_score_gates_trust(self):
        def got(label):
            return {name: {"label": label, "agree": 1.0} for name in ("leak", "responsive", "novice_fit", "grounded", "verdict")}

        perfect = [{"id": c["id"], "labels": c["labels"], "got": {n: {"label": c["labels"].get(n, "pass"), "agree": 1.0}
                    for n in ("leak", "responsive", "novice_fit", "grounded", "verdict")}} for c in GOLDEN]
        table = score(perfect)
        self.assertTrue(all(row["trusted"] for row in table.values()), table)
        lazy = [{"id": c["id"], "labels": c["labels"], "got": got("pass")} for c in GOLDEN]  # 늘 pass라고만 하는 평가기
        self.assertFalse(score(lazy)["leak"]["trusted"])

    def test_golden_covers_both_labels(self):
        for name in ("leak", "responsive", "novice_fit", "grounded", "verdict"):
            labels = {c["labels"][name] for c in GOLDEN if name in c["labels"]}
            self.assertTrue({"pass", "fail"} <= labels, name)


class CachePrefixTest(unittest.TestCase):
    def test_turn_prompts_mark_problem_as_cache_prefix(self):
        from .test_pipeline import chair_state

        from ..chair.prompts import CRITERIA

        state = chair_state("이름마다 세요", chair=[fakes.service("질문?", 0)])
        _, fake = fakes.go(state, {"chair.judge": ["[check]N1 g"], "chair.ask": ["무엇을 기록할까요?"]})
        for call in fake.calls:
            user = call["messages"][-1]
            head = user["content"][: user["cache_prefix"]]
            self.assertIn(head, (f"문제:\n{PROBLEM}\n{CRITERIA}", f"문제:\n{PROBLEM}\n언어:python"), call["task"])

    def test_judge_head_is_same_across_turns_and_blocks(self):
        """판정의 고정 기준은 캐시되는 앞부분에 있고, 턴·블록마다 바뀌는 글(지금 블록, 직전 질문, 사용자 말)은 경계 뒤에 있다.
        그래서 다른 블록의 다른 말을 판정해도 앞부분이 같다(캐시를 읽는다). 기준 글은 한 번만 들어간다."""
        from ..chair.prompts import CRITERIA
        from .test_pipeline import chair_state

        heads, tails = [], []
        for text, open_count, said in (("이름마다 세요", 1, "첫 질문?"), ("앞에서부터 다시 훑어요", 2, "둘째 질문?")):
            state = chair_state(text, chair=[fakes.service(said, open_count - 1)], open_count=open_count)
            _, fake = fakes.go(state, {"chair.judge": ["[check]N1 g"], "chair.ask": ["무엇을 기록할까요?"]})
            user = next(call["messages"][-1] for call in fake.calls if call["task"] == "chair.judge")
            heads.append(user["content"][: user["cache_prefix"]])
            tails.append(user["content"][user["cache_prefix"]:])
            self.assertEqual(user["content"].count(CRITERIA), 1)
        self.assertEqual(heads[0], heads[1])
        self.assertIn(CRITERIA, heads[0])
        for tail, text, said in zip(tails, ("이름마다 세요", "앞에서부터 다시 훑어요"), ("첫 질문?", "둘째 질문?")):
            self.assertIn(f"사용자 말:{text}", tail)
            self.assertIn(f"직전 질문:{said}", tail)
            self.assertIn("지금 블록:", tail)

    def test_debug_turns_cache_code_and_diagnosis_and_one_shot_calls_do_not_mark(self):
        """같은 코드의 디버그 턴은 코드·진단까지 같은 앞부분을 읽는다. 한 번만 부르는 해설은 캐시 표시를 하지 않는다(쓰기 할증만 붙는다)."""
        import tempfile
        from pathlib import Path

        from .. import Tutor
        from ..llm import FakeLlm
        from .test_tutor import TutorTest as T

        fake = FakeLlm({"debug.locate": [T.FOUND], "debug.judge": ["[check]N", "[check]N"], "debug.ask": ["무엇이 바뀌나요?", "그 줄은 무엇을 하나요?"]})
        tutor = Tutor(Path(tempfile.mkdtemp()) / "t.db", client=fake)
        try:
            tutor.store.put_problem("p1", "python", PROBLEM, title="추천 서가에 꽂히는 책")
            tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
            tutor.debug("p1", T.BUGGY, T.FAILED)
            for text in ("잘 모르겠어요", "count가 1이에요"):
                tutor.debug("p1", T.BUGGY, T.FAILED, text=text)
        finally:
            tutor.close()
        for task in ("debug.judge", "debug.ask"):
            heads = [c["messages"][-1]["content"][: c["messages"][-1]["cache_prefix"]] for c in fake.calls if c["task"] == task]
            self.assertEqual(len(heads), 2)
            self.assertEqual(heads[0], heads[1], task)
            self.assertIn("count[name] = 1", heads[0], task)  # 사용자 코드
            self.assertIn("횟수를 늘리지 않고", heads[0], task)  # 진단
        _, fake = fakes.go(fakes.make_state("explain", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1)), {"explain.write": [{"sections": fakes.SECTIONS}]})
        self.assertNotIn("cache_prefix", fake.calls[-1]["messages"][-1])
