"""질문 유형 고르기 표(의자·가이드). 모델 없음."""

import unittest
from dataclasses import replace

from . import fakes
from ..common.talk_rules import RETRY_LEAD, open_lead

OPEN_LEAD = open_lead("chair", "loop")  # 시험 계획의 둘째 블록은 반복이다
from ..state import TurnContext, Verdict
from ..turn.moves import FOUND_OK, FOUND_TIP, HINTS_DONE_UNFOUND, WRITE_TIP, WRITE_TIP_LAST, pick_move

PLAN = fakes.planned(fakes.hinted())


def turn(event="message", text="", used=(), index=0, last="없음", seen=None):
    """seen: 이미 낸 저장 힌트 수(주지 않으면 사다리 질문 수와 같다고 본다)."""
    count = sum(m in ("open", "clue", "trace", "blank", "tool", "shape") for m in used) if seen is None else seen
    return TurnContext(index=index, block=PLAN.blocks[index], last_question=last, recent=[], moves_used=list(used), event=event, text=text,
                       hints_seen=count)


class ChairMoveTest(unittest.TestCase):
    def pick(self, verdict, **kwargs):
        return pick_move("chair", PLAN, turn(**kwargs), verdict)

    def test_start_uses_saved_open(self):
        got = self.pick(None, event="start")
        self.assertEqual((got.move, got.advance, got.saved), ("open", False, fakes.HINTS1[0]))

    def test_found_with_guess_asks_basis_once(self):
        plan = fakes.planned(fakes.thinking())

        def at(**kwargs):
            base = dict(index=0, block=plan.blocks[0], last_question="없음", recent=[], moves_used=["open"], event="message", text="이름을 세면 돼요")
            return TurnContext(**{**base, **kwargs})

        got = pick_move("chair", plan, at(), Verdict(True, basis="g"))
        self.assertEqual((got.move, got.advance, got.saved), ("basis", False, None))
        asked = pick_move("chair", plan, at(basis_asked=True), Verdict(True, basis="g"))  # 문항에 한 번만
        self.assertEqual((asked.move, asked.advance), ("open", True))
        variable = self.pick(Verdict(True, basis="g"), text="이름을 세면 돼요", used=["open"])  # 변수 블록에서는 묻지 않는다
        self.assertEqual((variable.move, variable.advance, variable.target, variable.lead, variable.saved), ("open", True, 1, FOUND_TIP + OPEN_LEAD, fakes.HINTS2[0]))

    def test_found_with_basis_advances(self):
        got = self.pick(Verdict(True, basis="t"), text="문제에 제목이 같으면 같은 책이라고 있어서요")
        self.assertEqual((got.move, got.target, got.advance), ("open", 1, True))
        last = pick_move("chair", PLAN, turn(index=1), Verdict(True, basis="e"))
        self.assertEqual((last.move, last.advance, last.saved), ("recap", True, None))

    def test_missing_minor_signal_is_edge(self):
        got = self.pick(Verdict(False, miss=2), text="이름별로 세요")
        self.assertEqual((got.move, got.missing_signal), ("edge", "같은 글자가 여러 번 나오는 경우를 다룬다"))

    def test_claim_is_assumed_once_then_ladder(self):
        long_claim = "한 번씩만 세면 될 것 같아요"
        got = self.pick(Verdict(False, miss=1), text=long_claim, used=["open"])
        self.assertEqual((got.move, got.missing_signal), ("assume", "글자별로 센다"))
        after = self.pick(Verdict(False, miss=1), text=long_claim, used=["open", "assume"])
        self.assertEqual((after.move, after.saved), ("clue", None))  # 사용자 말을 받아 새로 묻는다

    def test_empty_answer_gets_next_saved_hint(self):
        """'모르겠어요' 뒤에 모델이 지은 말이 블록의 답을 말했다. 내용 없는 답에는 다음 번호 저장 힌트, 다 냈으면 고정 말(모델 0회)."""
        second = self.pick(Verdict(False), text="몰라요", used=["open"])
        self.assertEqual((second.move, second.saved), ("clue", fakes.HINTS1[1]))
        third = self.pick(Verdict(False), text="몰라요", used=["open", "clue"])
        self.assertEqual((third.move, third.saved), ("trace", fakes.HINTS1[2]))
        done = self.pick(Verdict(False), text="몰라요", used=["open", "clue", "trace"])
        self.assertEqual((done.saved, done.lead), (HINTS_DONE_UNFOUND, ""))  # 아직 찾지 못한 블록에는 코드 칸이 없다
        asked = self.pick(Verdict(False, aside="A"), text="답 알려 주세요", used=["open", "clue", "trace"])
        self.assertEqual((asked.lead, asked.saved), ("답 코드는 드리지 않아요. ", HINTS_DONE_UNFOUND))  # 같은 '이 블록 채우기' 안내는 한 번만

    def test_confused_long_answer_gets_help_not_assume(self):
        got = self.pick(Verdict(False, miss=1), text="모르겠어요, 반복문으로 하나씩 보면 될지 감이 안 와요", used=["open"])
        self.assertEqual(got.move, "clue")

    def test_opening_events_use_saved_hint(self):
        start = self.pick(None, event="start")
        self.assertEqual((start.move, start.saved, start.lead), ("open", fakes.HINTS1[0], ""))
        opened = self.pick(None, event="next")  # 채우기로 열린 블록의 첫 질문
        self.assertEqual((opened.move, opened.saved, opened.lead), ("open", fakes.HINTS1[0], open_lead("chair", "")))  # 시험 블록의 참고 코드는 새로 만드는 이름이 없어 종류를 말하지 않는다
        named = fakes.planned([replace(PLAN.blocks[0], reference="count = 0"), PLAN.blocks[1]])  # 변수를 만드는 블록은 종류를 말한다
        self.assertEqual(pick_move("chair", named, turn(event="next"), None).lead, open_lead("chair", "var_from_problem"))

    def test_malformed_verdict_is_n_and_climbs_ladder(self):
        got = self.pick(Verdict(False, malformed=True), text="네", used=["open"])
        self.assertEqual((got.move, got.advance), ("clue", False))
        long_text = self.pick(Verdict(False, malformed=True), text="글자를 하나씩 세면 될 것 같아요", used=["open"])
        self.assertEqual(long_text.move, "clue")  # 긴 말이어도 형식 오류는 사다리

    def test_block_code(self):
        ok = self.pick(Verdict(True), event="block_filled")
        self.assertEqual((ok.move, ok.advance, ok.lead), ("open", True, OPEN_LEAD))
        no = self.pick(Verdict(False, miss=1), event="block_filled", used=["open"])  # 고정 앞말 + 다음 번호 저장 힌트(모델 0회)
        self.assertEqual((no.move, no.advance, no.lead, no.saved), ("clue", False, RETRY_LEAD, fakes.HINTS1[1]))
        found = pick_move("chair", PLAN, turn(event="block_filled"), Verdict(True), found=True)  # 의자에서 이미 찾은 블록: 맞는지만, 진행은 그대로
        self.assertEqual((found.move, found.advance, found.saved, found.target), ("done", False, FOUND_OK, 0))
        missed = pick_move("chair", PLAN, turn(event="block_filled", used=["open"]), Verdict(False, miss=2), found=True)
        self.assertEqual((missed.move, missed.advance, missed.saved), ("done", False, RETRY_LEAD + fakes.HINTS1[1]))  # 확인 항목(답)을 인용하지 않는다


class GuideMoveTest(unittest.TestCase):
    def pick(self, verdict, **kwargs):
        return pick_move("guide", PLAN, turn(**kwargs), verdict)

    def test_opening_uses_saved_hint_and_content_is_generated(self):
        self.assertEqual((self.pick(None, event="start").move, self.pick(None, event="start").saved), ("blank", fakes.HINTS1[0]))
        self.assertEqual(self.pick(Verdict(False), text="모르겠어요", used=["blank"]).saved, fakes.HINTS1[1])
        self.assertEqual(self.pick(Verdict(False, miss=1), text="세요", used=["blank"]).move, "tool")
        self.assertEqual(self.pick(Verdict(False, miss=1), text="세요", used=["blank", "tool"]).move, "shape")
        self.assertEqual(self.pick(Verdict(False, miss=1), text="세요", used=["blank", "tool", "shape"]).move, "shape")

    def test_no_basis_or_assume(self):
        found = self.pick(Verdict(True, basis="g"), text="count[p] += 1")  # 말로 맞혀도 다음 블록을 열지 않는다: 코드 칸에 적어 확인받게 한다
        self.assertEqual((found.move, found.advance, found.target, found.lead, found.saved), ("write", False, 0, "", WRITE_TIP))
        missed = self.pick(Verdict(False, miss=2), text="이름마다 몇 번인지 센다고 생각해요", used=["blank"])
        self.assertEqual(missed.move, "tool")
        last = pick_move("guide", PLAN, turn(index=1), Verdict(True))
        self.assertEqual((last.move, last.advance), ("write", False))
        self.assertEqual(last.saved, WRITE_TIP_LAST)  # 마지막 블록에는 '다음 블록이 열려요'라고 하지 않는다
        filled = pick_move("guide", PLAN, turn(event="block_filled", text=""), Verdict(True))  # 코드 확인이 통과해야 연다
        self.assertEqual((filled.move, filled.advance, filled.target), ("blank", True, 1))
