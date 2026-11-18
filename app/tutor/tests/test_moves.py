"""질문 유형 고르기 표(의자·가이드). 모델 없음."""

import unittest
from dataclasses import replace

from . import fakes
from ..common.talk_rules import RETRY_LEAD, open_lead

OPEN_LEAD = open_lead("chair", "loop")  # 시험 계획의 둘째 블록은 반복이다
from ..state import TurnContext, Verdict
from ..turn.moves import FOUND_OK, HINTS_DONE, WRITE_TIP, WRITE_TIP_LAST, pick_move

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
        self.assertEqual((asked.move, asked.advance, asked.saved), ("write", False, WRITE_TIP))
        variable = self.pick(Verdict(True, basis="g"), text="이름을 세면 돼요", used=["open"])  # 변수 블록에서는 묻지 않는다
        self.assertEqual((variable.move, variable.advance, variable.target, variable.saved), ("write", False, 0, WRITE_TIP))

    def test_found_by_words_writes_not_advances(self):
        """의자에서 말로 맞혀도 다음 블록을 열지 않는다: 그 블록의 코드 칸에 적으라는 고정 말(모델 0회). 마지막 블록은 마지막 블록의 말."""
        got = self.pick(Verdict(True, basis="t"), text="문제에 제목이 같으면 같은 책이라고 있어서요")
        self.assertEqual((got.move, got.target, got.advance, got.saved), ("write", 0, False, WRITE_TIP))
        last = pick_move("chair", PLAN, turn(index=1), Verdict(True, basis="e"))
        self.assertEqual((last.move, last.target, last.advance, last.saved), ("write", 1, False, WRITE_TIP_LAST))
        asked = self.pick(Verdict(True, basis="t"), text="이름마다 세면 되나요?")  # 물음 꼴: 가이드처럼 스스로 확인하게 묻는다
        self.assertEqual((asked.move, asked.advance, asked.saved), ("verify", False, None))
        answered = self.pick(Verdict(False), text="3이 나와요", used=["open", "verify"])  # 확인 질문에 평서로 답했다
        self.assertEqual((answered.move, answered.advance, answered.saved), ("write", False, WRITE_TIP))

    def test_basis_answer_writes_or_is_judged(self):
        """근거 질문의 답: 평서면 코드로 적으라는 고정 말, 물음 꼴이면 판정대로(넘기지 않는다)."""
        plain = self.pick(None, text="문제에 제목이 같으면 같은 책이라고 해서요", used=["open", "basis"])
        self.assertEqual((plain.move, plain.advance, plain.saved), ("write", False, WRITE_TIP))
        asked = self.pick(Verdict(True, basis="t"), text="문제에 그렇게 적혀 있지 않나요?", used=["open", "basis"])
        self.assertEqual((asked.move, asked.advance), ("verify", False))
        wrong = self.pick(Verdict(False, miss=1), text="그냥 짐작인데 맞나요?", used=["open", "basis"])
        self.assertFalse(wrong.advance)

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
        self.assertEqual((done.saved, done.lead), (HINTS_DONE, ""))  # 아직 찾지 못한 블록에도 코드 칸이 있다
        asked = self.pick(Verdict(False, aside="A"), text="답 알려 주세요", used=["open", "clue", "trace"])
        self.assertEqual((asked.lead, asked.saved), ("답 코드는 드리지 않아요. ", HINTS_DONE))  # 같은 '이 블록 채우기' 안내는 한 번만

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


class BeginnerMoveTest(unittest.TestCase):
    """입문자가 '그게 뭐예요?'라고 물으면 되묻기만 했고, '너무 어려워요'에 같은 질문을 되풀이했다."""

    def test_term_question_gets_meaning_then_returns(self):
        for mode in ("chair", "guide"):
            got = pick_move(mode, PLAN, turn(text="그게 뭐예요?", used=["open"]), Verdict(False, aside="Q"))
            self.assertEqual((got.move, got.advance, got.target, got.saved, got.lead), ("term", False, 0, None, ""), mode)  # 모델이 뜻과 예를 짓는다

    def test_term_during_verify_keeps_the_way_to_write(self):
        """확인 질문(verify) 중에 낱말의 뜻을 물었다(term). 뜻을 들은 뒤 답하면 처음 생각은 이미 맞았으니 코드로 적게 한다(그 길을 놓쳤다)."""
        asked = pick_move("guide", PLAN, turn(text="range가 뭐예요?", used=["blank", "verify"]), Verdict(False, aside="Q"))
        self.assertEqual(asked.move, "term")
        after = pick_move("guide", PLAN, turn(text="0부터 n-1까지 돌아요", used=["blank", "verify", "term"]), Verdict(False))
        self.assertEqual((after.move, after.saved), ("write", WRITE_TIP))

    def test_too_hard_gets_smaller_saved_hint(self):
        from ..common.talk_rules import HARD_LEAD

        got = pick_move("chair", PLAN, turn(text="너무 어려워요", used=["open"]), None)
        self.assertEqual((got.lead, got.saved), (HARD_LEAD, fakes.HINTS1[1]))  # 다음 저장 힌트가 한 칸 더 작은 질문이다
        from ..turn.moves import empty_answer, hard, rule_verdict

        for text in ("그게 뭔지 몰라요", "변수가 뭔지 몰라요", "변수가 뭐예요?", "무슨 뜻이에요?"):  # 뜻 묻기는 판정(W)으로 넘긴다
            self.assertIsNone(rule_verdict(text), text)
        for text in ("너무 어려워요", "어렵네요", "이해가 안 돼요"):
            self.assertTrue(hard(text) and empty_answer(text), text)
        for text in ("어려운 건 없고 이름별로 세면 될 것 같아요", "어렵지 않아요", "안 어려워요", "어려서부터 쓰던 말"):
            self.assertFalse(hard(text), text)
        plain = pick_move("chair", PLAN, turn(text="모르겠어요", used=["open"]), None)
        self.assertEqual((plain.lead, plain.saved), ("", fakes.HINTS1[1]))  # 어렵다는 말이 없으면 앞말도 없다


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

    def test_right_idea_asked_as_question_is_not_write_tip(self):
        """맞는 생각을 물음으로 냈다: 코드로 적으라는 고정 말(물음에 답하지 않는다) 대신 모델이 스스로 확인할 질문을 짓는다. 맞다고 말하지 않는다."""
        for text in ("처음부터 끝까지 range로 돌려야 하나요?", "이름마다 세면 될까", "count에 1을 더하면 되죠"):
            got = self.pick(Verdict(True), text=text, used=["blank"])
            self.assertEqual((got.move, got.advance, got.saved), ("verify", False, None), text)
        said = self.pick(Verdict(True), text="이름마다 1씩 더해서 세요", used=["blank"])  # 말로 맞힌 생각은 그대로 코드로 적게 한다
        self.assertEqual((said.move, said.saved), ("write", WRITE_TIP))
        traced = self.pick(Verdict(False), text="owl이 2가 돼요", used=["blank", "verify"])  # 확인 질문에 답했다: 처음 생각이 맞았으니 코드로 적게 한다
        self.assertEqual((traced.move, traced.saved), ("write", WRITE_TIP))
        for text in ("이름마다 세어 가요", "같은 이름이 또 나오니까 1을 더해요", "다 세고 나면 돌려줘요"):  # 물음 어미가 아닌 평서문
            self.assertEqual(self.pick(Verdict(True), text=text, used=["blank"]).move, "write", text)
        for text in ("이름별로 세는 건가요", "1부터 시작하는가요", "range로 돌려도 될까"):
            self.assertEqual(self.pick(Verdict(True), text=text, used=["blank"]).move, "verify", text)
        twice = self.pick(Verdict(True), text="그럼 1을 더하면 되나요?", used=["blank", "verify", "blank"])  # 확인 질문은 블록에 한 번만
        self.assertEqual((twice.move, twice.saved), ("write", WRITE_TIP))
        again = self.pick(Verdict(False), text="모르겠어요", used=["blank", "verify"])
        self.assertEqual(again.saved, fakes.HINTS1[1])  # 내용 없는 답은 전과 같이 저장 힌트
