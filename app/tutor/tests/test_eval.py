"""평가기 시험: 규칙 검사, 모델 평가기 표 세기(근거 검증·다수결), 보정 지표, 캐시 경계 표시."""

import unittest
from types import SimpleNamespace

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


RESULT = "이 코드로는 아직 넘어가지 않아요. 공개 예시로만 확인했어요."
QUESTION = "loans를 처음부터 훑을 때 같은 제목이 한 번 더 나오면 기록해 둔 무엇을 바꿔야 할까요?"
NOTE = "제목이 같으면 같은 책으로 보셨어요."
WAY = "막혔다면 이 블록 채우기로 코드를 받아 보고 넘어가도 돼요."


def parted(question=QUESTION, note=NOTE):
    """결과 → 질문 → 근거 → 길 안내 줄로 된 튜터 말과 그 칸(길 안내 줄은 칸에 넣지 않는다)."""
    parts = {"block_index": 0, "result": RESULT, "question": question, **({"note": note} if note else {})}
    return row("\n".join(x for x in (RESULT, question, note, WAY) if x), parts=parts)


class PartsTest(unittest.TestCase):
    """기록에 튜터 말의 칸이 있으면 질문·근거 기준을 칸마다 잰다. 칸이 없는 옛 기록은 말 전체로 잰다."""

    def test_record_keeps_reply_parts(self):
        from ..eval import drive
        from ..state import ChatMessage

        parts = {"block_index": 0, "result": RESULT, "question": QUESTION, "buttons": ["fill"]}
        said = ChatMessage(id="m1", role="service", text=f"{RESULT}\n{QUESTION}\n{WAY}", at="", block_index=0, move="clue", parts=parts)
        ctx = SimpleNamespace(chair=[said], guide=[], plan=None, open_count=1)
        s = drive.Session.__new__(drive.Session)
        s.scenario, s.mode, s.rows, s.visible, s.filled = SimpleNamespace(id="p1", text=PROBLEM), "chair", [], [], {}
        s.tutor = SimpleNamespace(store=SimpleNamespace(load=lambda _pid: ctx), turn=lambda *a, **k: SimpleNamespace(status=200, body={}))
        s.start()
        self.assertEqual(s.rows[-1]["parts"], parts)
        self.assertEqual(s.rows[-1]["reply"], said.text)

    def test_parts_keep_result_and_way_lines_out_of_question(self):
        got = parted()
        self.assertGreater(len(got["reply"]), 120)  # 말 전체는 길고 네 문장을 넘지만 질문 칸은 한 문장이다
        flags = checks.reply_flags(got, None)
        self.assertNotIn("3문장 초과", flags)
        self.assertEqual([f for f in flags if "칸" in f], [], flags)

    def test_parts_measure_question_and_note(self):
        self.assertIn("질문 칸 여러 문장", checks.reply_flags(parted("제목을 세면 어떨까요? 그 값은 어디에 둘까요?"), None))
        self.assertIn("질문 칸 길이", checks.reply_flags(parted("책 제목을 " * 25 + "셀까요?"), None))
        self.assertIn("근거 칸 길이", checks.reply_flags(parted(note="같은 제목은 같은 책으로 보고 " * 6 + "센다."), None))
        self.assertIn("근거 칸 여러 문장", checks.reply_flags(parted(note="같은 책이에요. 한 번만 꽂아요."), None))

    def test_old_rows_without_parts_are_measured_as_before(self):
        old = parted()
        old.pop("parts")
        flags = checks.reply_flags(old, None)
        self.assertIn("3문장 초과", flags)
        self.assertEqual([f for f in flags if "칸" in f], [])
        self.assertIsNone(checks.session_metrics(checks.annotate([old]), [])["slot_clean_rate"])

    def test_slot_result_in_metrics_report_and_compare_with_mixed_rows(self):
        import copy

        from ..eval import compare, qa

        old = parted()
        old.pop("parts")
        rows = [parted(), parted("제목을 세면 어떨까요? 그 값은 어디에 둘까요?"), old]
        got = checks.session_metrics(checks.annotate(copy.deepcopy(rows)), [])
        self.assertEqual(got["slot_clean_rate"], 0.5)  # 칸이 있는 두 말 가운데 하나만 칸 기준을 지켰다
        text = qa.report([{**got, "session": "s1"}], {}, {})
        self.assertEqual(sum(line.startswith("| slot_clean_rate") for line in text.splitlines()), 1)
        self.assertEqual(compare.numbers(copy.deepcopy(rows))["slot_clean_rate"], 0.5)  # 칸 있는 줄과 없는 줄이 섞인 기록
        self.assertIsNone(compare.numbers([copy.deepcopy(old)])["slot_clean_rate"])


MISS = {"decision": "못 찾음", "move": "clue", "advance": False}


class FakeSession:
    """play()가 부르는 Session의 자리(모델·저장소 없음). say는 대본대로 답하고, 부른 차례를 log에 남긴다."""

    def __init__(self, script):
        self.script, self.log, self.rows, self.visible, self.filled = list(script), [], [], [], {}

    def __call__(self, scenario, mode):
        return self

    def start(self):
        self.rows.append({"kind": "turn", "event": "start", "status": 200})

    def ctx(self):
        return SimpleNamespace(plan=SimpleNamespace(blocks=["b1", "b2", "b3"]))

    def say(self, text):
        self.log.append(text)
        row = {"kind": "turn", "event": "message", "status": 200, **(self.script.pop(0) if self.script else MISS)}
        self.rows.append(row)
        return row

    def check(self):
        self.log.append("check")
        return {"status": 200, "passed": True, "last": True, "move": None}

    def fill(self):
        self.log.append("fill")
        return {"status": 200, "hidden": {"index": 2}}  # 마지막 블록을 채웠다: 코드 쓰기로

    def next(self):
        self.log.append("next")

    def submit(self, code):
        return {"ok": True}

    def feedback(self):
        pass

    def explain(self):
        pass


class PlayAskTest(unittest.TestCase):
    """같은 블록에서 3번 막히면 한 번 튜터 말을 되묻는다. 그 말도 메인 대화 턴이라 결과(넘김·write)를 보통 턴처럼 따른다."""

    def play(self, script):
        from unittest import mock

        from ..eval import drive

        fake = FakeSession(script)
        said = lambda scenario, visible, what: "ASK" if "되묻" in what else "ANSWER"  # noqa: E731
        with mock.patch.multiple(drive, Session=fake, novice_say=said, novice_code=lambda *a: ""):
            drive.play(SimpleNamespace(id="p1"))
        return fake

    def test_block_passed_on_ask_counts_again_in_the_new_block(self):
        fake = self.play([MISS] * 3 + [{"decision": "찾음", "move": "open", "advance": True}])
        # 새 블록에서는 처음부터 다시 센다: 3번 막히면 되묻고, 되묻기를 빼고 5번째 막힘에서 채운다
        self.assertEqual(fake.log, ["ANSWER"] * 3 + ["ASK"] + ["ANSWER"] * 3 + ["ASK"] + ["ANSWER"] * 2 + ["fill"])
        self.assertEqual([r.get("ask", False) for r in fake.rows[1:]], [False] * 3 + [True] + [False] * 3 + [True] + [False] * 2)
        got = checks.session_metrics(fake.rows, [])
        self.assertEqual((got["user_turns"], got["max_stuck"]), (8, 5))  # 되묻는 말은 사용자 턴과 막힘에 넣지 않는다

    def test_write_on_ask_goes_to_block_check(self):
        fake = self.play([MISS] * 3 + [{"decision": "찾음", "move": "write", "advance": False}])
        self.assertEqual(fake.log, ["ANSWER"] * 3 + ["ASK", "check"])


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

        state = chair_state("이름마다 세요", chair=[fakes.service("질문?", 0)])
        _, fake = fakes.go(state, {"chair.judge": ["[check]N1 g"], "chair.ask": ["무엇을 기록할까요?"]})
        for call in fake.calls:
            user = call["messages"][-1]
            head = user["content"][: user["cache_prefix"]]
            self.assertIn(head, (f"문제:\n{PROBLEM}", f"문제:\n{PROBLEM}\n언어:python"), call["task"])

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
