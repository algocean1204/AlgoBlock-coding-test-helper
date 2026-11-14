"""튜터 그래프 흐름(가짜 모델). 저장소 대신 문맥을 직접 넣고 저장은 바꿔 끼운다."""

import json
import unittest
from dataclasses import replace

from . import fakes
from ..common.talk_prompts import CONCEPT_FIRST
from ..common.talk_rules import reply_problems, sentences
from ..common.talk_rules import (ALL_FILLED, ALONE_OK, ANSWER_LEAD, BACK_LEAD, EXAMPLES_ONLY, FALLBACK, MALFORMED, RETRY_LEAD, SKIPPED, UNRUN_NO,
                                UNVERIFIED, open_lead)

OPEN_LEAD = open_lead("chair", "loop")  # 시험 계획의 둘째 블록은 반복이다
from ..llm import LlmFailed, LlmTimeout
from ..main import AGENTS, build
from ..state import BlockState, DebugState, FilledBlock, Solution, Submission
from ..turn.code_check import BRACE_CLOSE, BRACE_OPEN, NOT_JOINED, brace_note, code_hash, unrun_note
from ..turn.moves import FOUND_OK, FOUND_TIP, HINTS_DONE, HINTS_DONE_UNFOUND

DRAFT = {"plan.draft_blocks": [fakes.drafted([fakes.as_dict(b) for b in fakes.hinted()])]}


def chair_state(text=None, event="message", chair=(), open_count=1, plan=None, **extra):
    ctx = fakes.context(plan=plan or fakes.planned(fakes.hinted()), open_count=open_count, chair=list(chair), **extra)
    return fakes.make_state("turn", ctx, mode="chair", event=event, text=text, **({"block_id": "b1", "code": text} if event == "block_filled" else {}))


class PlanTest(unittest.TestCase):
    def test_plan_made_once_then_reused(self):
        done, fake = fakes.go(fakes.make_state("explain", fakes.context()), {**DRAFT, "explain.write": [{"sections": fakes.SECTIONS}]})
        self.assertIsNone(done.get("error"))
        self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks", "explain.write"])  # 풀이 가이드가 먼저다(가짜 모델에 없으면 가이드 없이 간다)
        self.assertEqual((done["plan"].strategy, done["plan"].algorithm, done["open_count"]), ("fresh", "hash", 1))
        self.assertEqual(done["plan"].blocks[0].hints, fakes.HINTS1)
        draft = fakes.prompt(fake, "plan.draft_blocks")
        for must in ("이분탐색", "작은따옴표로 그대로 인용", "질문은 하나만 한다", "블록 설계 가이드"):
            self.assertIn(must, draft)
        self.assertNotIn("사용자 코드:", draft)
        written = fakes.prompt(fake, "explain.write")
        self.assertIn("풀이 유형:해시", written)
        self.assertIn("1. 입력받기 (문제에서 바로 오는 변수) — 목표-입력받기", written)
        self.assertNotIn("var_from_problem", written)  # 영어 블록 종류를 모델에 넘기지 않는다
        self.assertIn("끝에 블록을 이은 전체 코드", written)  # 가이드가 없으면 모델이 블록을 이어 쓴다

        again, fake = fakes.go(fakes.make_state("explain", fakes.context(plan=done["plan"], open_count=1)), {"explain.write": [{"sections": fakes.SECTIONS}]})
        self.assertEqual(fakes.tasks(fake), ["explain.write"])
        self.assertEqual(again["response"]["status"], 200)

    def test_explain_does_not_copy_the_guide_code(self):
        """가이드가 있으면 해설은 전체 코드를 옮겨 쓰지 않는다(출력 토큰을 아낀다). 코드 없이 온 네 절은 그대로이고, 마지막 절 끝에 가이드 코드가 붙는다."""
        from ..state import Solution

        guide = Solution(approach="센다", steps=["센다"], code="def solution(a, b):\n    return 0", verified=True, clues=[])
        done, fake = fakes.go(fakes.make_state("explain", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1, solution=guide)), {"explain.write": [{"sections": fakes.SECTIONS}]})
        written = fakes.prompt(fake, "explain.write")
        self.assertIn("전체 코드는 쓰지 않는다", written)
        self.assertNotIn("끝에 블록을 이은 전체 코드", written)
        sections = done["result"]["explain"].sections
        self.assertEqual([section.title for section in sections], [row["title"] for row in fakes.SECTIONS])
        self.assertEqual(sections[-1].body, "이어서\n\n```python\ndef solution(a, b):\n    return 0\n```")

    def test_strategy_follows_score_and_keep_flow_shows_code(self):
        rows = [("[check]49 Y", "canonical"), ("[check]50 Y", "keep_flow"), ("[check]80 N", "canonical")]
        for verdict, strategy in rows:
            with self.subTest(verdict=verdict):
                done, fake = fakes.go(fakes.make_state("explain", fakes.context(direct_code="print(1)")),
                                      {"plan.assess": [verdict], **DRAFT, "explain.write": [{"sections": fakes.SECTIONS}]})
                self.assertEqual(done["plan"].strategy, strategy)
                self.assertIn("채점 기준표", fakes.prompt(fake, "plan.assess"))
                self.assertEqual("사용자 코드:\nprint(1)" in fakes.prompt(fake, "plan.draft_blocks"), strategy == "keep_flow")
                self.assertEqual(fake.calls[0]["params"]["max_tokens"], 16)

    def test_plan_failures_stop_before_feature(self):
        bad_kind = fakes.drafted([{**fakes.as_dict(fakes.two()[0]), "kind": "output"}])
        cases = [
            ({"plan.assess": ["62점"]}, "invalid_output", "print(1)"),
            ({"plan.draft_blocks": [bad_kind]}, "invalid_output", ""),
            ({"plan.draft_blocks": [fakes.drafted([fakes.as_dict(b) for b in fakes.two()], "floyd")]}, "invalid_output", ""),
            ({"plan.draft_blocks": [{"algorithm": "hash"}]}, "llm_failed", ""),
        ]
        for scripts, code, direct in cases:
            with self.subTest(scripts=scripts):
                done, fake = fakes.go(fakes.make_state("explain", fakes.context(direct_code=direct)), scripts)
                self.assertEqual(done["error"].code, code)
                self.assertIsNone(done.get("plan"))
                self.assertNotIn("explain.write", fakes.tasks(fake))

    def test_out_of_scope_kept_hidden(self):
        done, _ = fakes.go(fakes.make_state("explain", fakes.context()),
                           {"plan.draft_blocks": [fakes.drafted([fakes.as_dict(b) for b in fakes.hinted()], "graph", True)],
                            "explain.write": [{"sections": fakes.SECTIONS}]})
        self.assertTrue(done["plan"].out_of_scope)


class ChairTest(unittest.TestCase):
    def test_start_uses_saved_question_without_model(self):
        done, fake = fakes.go(chair_state(event="start"), {})
        self.assertEqual(fake.calls, [])
        self.assertEqual(done["result"], {"reply": fakes.HINTS1[0], "advance": False, "move": "open"})

    def test_start_on_new_plan_costs_one_call(self):
        ctx = fakes.context()
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="chair", event="start"), DRAFT)
        self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks"])
        self.assertEqual(done["result"]["reply"], fakes.HINTS1[0])

    def test_guess_gets_basis_question(self):
        asked = "'이름을 세면 된다'는 생각은 문제 글의 어느 문장에서 나왔나요, 아니면 짐작인가요?"
        done, fake = fakes.go(chair_state("이름을 세면 돼요", chair=[fakes.service(fakes.HINTS1[0], 0)], plan=fakes.planned(fakes.thinking())),
                              {"chair.judge": ["[check]Y g"], "chair.ask": [asked]})
        self.assertEqual(fakes.tasks(fake), ["chair.judge", "chair.ask"])
        self.assertEqual(done["result"], {"reply": asked, "advance": False, "move": "basis"})
        judge = fakes.prompt(fake, "chair.judge")
        self.assertIn("근거 수준", judge)
        self.assertIn(f"직전 질문:{fakes.HINTS1[0]}", judge)
        for leak in ("REF_ONE", "NEXT_SECRET", "언어:", "깊이"):
            self.assertNotIn(leak, judge)
        ask = fakes.prompt(fake, "chair.ask")
        for must in ("판정을 먼저 말하지 않는다", "'근거' 질문 지시가 있을 때만", "좋아요", "질문 유형 지시: 사용자 주장 한 구절을 인용", "튜터: 책마다", "풀이 유형:해시",
                     CONCEPT_FIRST):  # 개념을 물으면 먼저 답한다
            self.assertIn(must, ask)
        for leak in ("REF_ONE", "REF_TWO", "NEXT_SECRET"):
            self.assertNotIn(leak, ask)

    def test_basis_then_advance_with_saved_next(self):
        talk = [fakes.service(fakes.HINTS1[0], 0, "m1"), fakes.user("이름을 세면 돼요", 0), fakes.service("근거는요?", 0, "m2", "basis")]
        done, fake = fakes.go(chair_state("문제에 제목이 같으면 같은 책이라고 해서요", chair=talk), {})
        self.assertEqual(fakes.tasks(fake), [])  # 근거 질문의 답은 판정하지 않고 넘어간다(모델 0회)
        self.assertEqual(done["result"], {"reply": FOUND_TIP + OPEN_LEAD + fakes.HINTS2[0], "advance": True, "move": "open"})
        self.assertEqual(done["open_count"], 2)

    def test_last_block_recap(self):
        plan = fakes.planned([fakes.hinted()[0]])
        done, fake = fakes.go(chair_state("문제 글에 그렇게 적혀 있어요", plan=plan), {"chair.judge": ["[check]Y t"], "chair.ask": ["처음부터 무엇을 정했는지 말해 볼까요?"]})
        self.assertEqual((done["result"]["move"], done["result"]["advance"], done["open_count"]), ("recap", True, 1))
        self.assertIn("처음부터 순서대로", fakes.prompt(fake, "chair.ask"))

    def test_after_recap_answer_close_without_model(self):
        plan = fakes.planned([fakes.hinted()[0]])
        talk = [fakes.service("처음부터 순서대로 말해 볼까요?", 0, "m1", "recap")]
        done, fake = fakes.go(chair_state("이름을 세고 남은 사람을 찾아요", plan=plan, chair=talk), {})
        self.assertEqual(fake.calls, [])  # 정리 질문의 답은 판정도 생성도 없이 코드로 보낸다
        self.assertEqual(done["result"]["move"], "close")
        self.assertTrue(done["result"]["reply"].endswith("?"))

    def test_claim_gets_assume_with_direction(self):
        done, fake = fakes.go(chair_state("한 번씩만 세면 될 것 같아요", chair=[fakes.service(fakes.HINTS1[0], 0)]),
                              {"chair.judge": ["[check]N1 g"], "chair.ask": ["'한 번씩만 세면 된다'고 했는데 같은 이름이 두 번이면요?"]})
        self.assertEqual(done["result"]["move"], "assume")
        self.assertIn("가리킬 방향: 글자별로 센다(그대로 말하지 않는다)", fakes.prompt(fake, "chair.ask"))

    def test_rule_breaking_reply_becomes_fallback(self):
        done, _ = fakes.go(chair_state("한 번씩만 세면 될 것 같아요", chair=[fakes.service(fakes.HINTS1[0], 0)]),
                           {"chair.judge": ["[check]N1"], "chair.ask": ["좋은 생각이에요! 다음은 NEXT_SECRET이에요."]})
        self.assertEqual(done["result"]["reply"], FALLBACK["assume"])

    def test_malformed_judge_climbs_ladder(self):
        done, fake = fakes.go(chair_state("네", chair=[fakes.service(fakes.HINTS1[0], 0)]),
                              {"chair.judge": ["Y입니다"], "chair.ask": ["'제목이 같으면 같은 책입니다'는 무엇을 뜻할까요?"]})
        self.assertEqual(fakes.tasks(fake), ["chair.judge", "chair.ask"])  # 사용자 말을 받아 새로 묻는다
        self.assertEqual(done["result"], {"reply": "'제목이 같으면 같은 책입니다'는 무엇을 뜻할까요?", "advance": False, "move": "clue"})

    def test_found_block_code_check_keeps_progress(self):
        """의자에서 이미 찾은 블록의 코드 확인: 맞으면 모델 0회로 맞다고만, 틀리면 판정 한 번 뒤 고정 앞말 + 그 블록의 다음 저장 힌트. 진행은 그대로. 가이드는 지금 블록만 받는다."""
        chair = [fakes.service(fakes.HINTS1[0], 0), fakes.user("이름별로 세요", 0), fakes.service(OPEN_LEAD + fakes.HINTS2[0], 1, "m2")]
        done, fake = fakes.go(chair_state("REF_ONE", event="block_filled", chair=chair, open_count=2), {})  # 참고 코드와 같다
        self.assertEqual((fake.calls, done["result"], done["open_count"], done["block_check"].block_id, done["block_check"].verdict),
                         ([], {"reply": FOUND_OK, "advance": False, "move": "done", "renamed": []}, 2, "b1", "Y"))
        done, fake = fakes.go(chair_state("x = 1", event="block_filled", chair=chair, open_count=2), {"chair.check_code": ["[check]N2"]})
        self.assertEqual((fakes.tasks(fake), done["result"]["reply"], done["result"]["advance"], done["open_count"]),
                         (["chair.check_code"], unrun_note("") + " " + UNRUN_NO + " " + fakes.HINTS1[1], False, 2))  # 확인 항목(답을 말한 문장)은 인용하지 않는다. 채점 함수가 없어 읽고 본 판단이라 그렇게 말한다
        guide = fakes.make_state("turn", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=2, guide=[fakes.service("빈칸?", 1)]),
                                 mode="guide", event="block_filled", block_id="b1", code="REF_ONE")
        done, fake = fakes.go(guide, {})  # 가이드도 앞 블록을 고쳐 다시 확인할 수 있다. 진행은 그대로
        self.assertEqual((fake.calls, done.get("error"), done["open_count"], done["result"]["reply"]), ([], None, 2, FOUND_OK))

    def test_block_code_judged_once_per_code(self):
        state = chair_state("rented = input().split()", event="block_filled")
        done, fake = fakes.go(state, {"chair.check_code": ["[check]Y"]})
        self.assertEqual(fakes.tasks(fake), ["chair.check_code"])
        # 채점 함수가 없어 모델이 코드를 읽고 통과시켰다: 그렇다고 말하고 '확인 전'으로 둔다(진행은 한다)
        self.assertEqual(done["result"]["reply"], unrun_note("") + " " + OPEN_LEAD + fakes.HINTS2[0])
        self.assertEqual((done["block_check"].verdict, done["block_check"].tries, done["open_count"]), ("?", 1, 2))
        checked = fakes.prompt(fake, "chair.check_code")
        self.assertIn("REF_ONE", checked)  # 비교 기준. 출력이 [check]뿐이라 새지 않는다
        self.assertNotIn("NEXT_SECRET", checked)

        saved = BlockState("b1", "x = 1", code_hash("x = 1"), "N", 1, 1)
        again = chair_state("\nx = 1 ", event="block_filled", block_states={"b1": saved}, chair=[fakes.service(fakes.HINTS1[0], 0)])  # 앞 빈 줄·끝 공백만 다르다
        done, fake = fakes.go(again, {})
        self.assertEqual(fakes.tasks(fake), [])  # 같은 코드라 판정은 0회, 말은 고정 앞말 + 다음 저장 힌트
        self.assertEqual(done["result"]["reply"], unrun_note("") + " " + UNRUN_NO + " " + fakes.HINTS1[1])  # 채점 함수가 없을 때의 지난 거절이라 읽고 본 판단이다('확인 전')
        self.assertEqual((done["block_check"].verdict, done["block_check"].tries), ("N", 1))  # 실행으로 확인한 틀림이 아니라 틀린 수는 그대로다

    def test_answer_request_and_off_topic_get_fixed_leads(self):
        chair = [fakes.service(fakes.HINTS1[0], 0)]
        done, fake = fakes.go(chair_state("그냥 답 코드 알려 줘", chair=chair), {})  # 짧은 답 요청은 규칙으로 가른다(모델 0회)
        self.assertEqual((fake.calls, done["result"]["reply"]), ([], ANSWER_LEAD + fakes.HINTS1[1]))
        done, fake = fakes.go(chair_state("이 문제 어떻게 푸는지 코드로 전부 보여 주실 수 있나요", chair=chair), {"chair.judge": ["[check]A"]})
        self.assertEqual((fakes.tasks(fake), done["result"]["reply"]), (["chair.judge"], ANSWER_LEAD + fakes.HINTS1[1]))  # 말은 저장 힌트(모델이 짓지 않는다)
        self.assertIn("[check]A", fakes.prompt(fake, "chair.judge"))
        done, fake = fakes.go(chair_state("오늘 점심 뭐 먹지", chair=chair), {"chair.judge": ["[check]O"]})
        self.assertEqual((fakes.tasks(fake), done["result"]["reply"]), (["chair.judge"], BACK_LEAD + fakes.HINTS1[1]))
        old = fakes.planned(fakes.two())  # 저장 힌트가 없는 옛 계획은 모델이 짓는다
        done, fake = fakes.go(chair_state("그냥 답 코드 알려 줘", chair=chair, plan=old), {"chair.ask": ["이름이 두 번 나오면 무엇을 적어 둘까요?"]})
        self.assertEqual(done["result"]["reply"], ANSWER_LEAD + "이름이 두 번 나오면 무엇을 적어 둘까요?")
        self.assertIn("답을 달라고 했다", fakes.prompt(fake, "chair.ask"))

    def test_two_empty_answers_get_fill_tip_once(self):
        """'모르겠어요'를 세 번 거듭해도 '이 블록 채우기' 길을 몰랐다. 두 번째 뒤에 한 번만 알린다."""
        from ..common.talk_rules import FILL_TIP

        chair = [fakes.service(fakes.HINTS1[0], 0, "m1"), fakes.user("모르겠어요", 0, "u1"), fakes.service("명단에서 무엇을 셀까요?", 0, "m2", "clue")]
        ask = {"chair.judge": ["[check]N1"], "chair.ask": ["s가 \"aa\"라면 무엇을 적어 둘까요?"]}
        done, fake = fakes.go(chair_state("잘 모르겠음", chair=chair), dict(ask))
        self.assertEqual((fake.calls, done["result"]["reply"]), ([], FILL_TIP + fakes.HINTS1[1]))  # 내용 없는 답: 판정도 말도 모델 0회
        third = chair + [fakes.user("잘 모르겠음", 0, "u2"), fakes.service(done["result"]["reply"], 0, "m3", "trace")]
        done, _ = fakes.go(chair_state("모르겠어요", chair=third), dict(ask))
        self.assertFalse(done["result"]["reply"].startswith(FILL_TIP))  # 한 블록에 한 번
        once = [fakes.service(fakes.HINTS1[0], 0, "m1"), fakes.user("이름을 세면 될 것 같은데 같은 이름은 잘 모르겠어요", 0, "u1"), fakes.service("명단에서 무엇을 셀까요?", 0, "m2", "clue")]
        done, _ = fakes.go(chair_state("모르겠어요", chair=once), dict(ask))
        self.assertFalse(done["result"]["reply"].startswith(FILL_TIP))  # 앞 말에 내용이 있었다

    def test_empty_answers_use_saved_hints_without_model(self):
        """의자도 '모르겠어요'·답 조름 뒤에 모델이 지은 말이 블록의 답을 말했다. 판정도 규칙으로 먼저 가른다(모델 0회)."""
        from ..common.talk_rules import FILL_TIP
        from ..turn.moves import rule_verdict

        for text in ("모르겠어요", "모르겠습니다", "잘 모르겠네요", "몰라요", "힌트 주세요", "답 알려 주세요", "정답 알려줘"):
            self.assertIsNotNone(rule_verdict(text), text)
        self.assertIsNone(rule_verdict("이름별로 세면 될 것 같아요"))
        talk, replies = [fakes.service(fakes.HINTS1[0], 0, "m0")], []
        for n, text in enumerate(("모르겠어요", "잘 모르겠습니다", "몰라요", "답 알려 주세요")):
            done, fake = fakes.go(chair_state(text, chair=talk), {})
            self.assertEqual(fake.calls, [], text)
            replies.append(done["result"]["reply"])
            talk = talk + [fakes.user(text, 0, f"u{n}"), fakes.service(replies[-1], 0, f"s{n}", done["result"]["move"])]
        self.assertEqual(replies, [fakes.HINTS1[1], FILL_TIP + fakes.HINTS1[2], HINTS_DONE_UNFOUND, "답 코드는 드리지 않아요. " + HINTS_DONE_UNFOUND])

    def test_model_failure_is_error(self):
        done, _ = fakes.go(chair_state("한 번씩만 세면 될 것 같아요"), {"chair.judge": ["[check]N1"], "chair.ask": [LlmTimeout("늦음")]})
        self.assertEqual(done["error"].code, "llm_timeout")
        self.assertIsNone(done.get("response"))

    def test_broken_position_stops_before_model(self):
        done, fake = fakes.go(chair_state("말", open_count=5), {})
        self.assertEqual((done["error"].message, fake.calls), ("지금 블록이 없습니다.", []))


class GuideTest(unittest.TestCase):
    def guide(self, text=None, event="message", guide=()):
        ctx = fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1, guide=list(guide))
        return fakes.make_state("turn", ctx, mode="guide", event=event, text=text)

    def test_guide_opens_with_saved_hints_and_never_asks_basis(self):
        """모델이 지은 블록 안내 말은 블록의 답을 문장으로 말하곤 했다. 여는 말과 내용 없는 답 뒤는 저장 힌트(모델 0회)."""
        done, fake = fakes.go(self.guide(event="start"), {})
        self.assertEqual((fake.calls, done["result"]["move"], done["result"]["reply"]), ([], "blank", fakes.HINTS1[0]))
        talk = [fakes.service(fakes.HINTS1[0], 0, "m1")]
        replies = []
        for n, text in enumerate(("모르겠어요", "모르겠어요", "모르겠어요", "답 알려 주세요")):
            done, fake = fakes.go(self.guide(text, guide=talk), {})
            self.assertEqual(fake.calls, [])
            replies.append(done["result"]["reply"])
            talk = talk + [fakes.user(text, 0, f"u{n}"), fakes.service(replies[-1], 0, f"s{n}", done["result"]["move"])]
        from ..common.talk_rules import FILL_TIP
        self.assertEqual(replies, [fakes.HINTS1[1], FILL_TIP + fakes.HINTS1[2], HINTS_DONE, "답 코드는 드리지 않아요. " + HINTS_DONE])
        done, fake = fakes.go(self.guide("이름마다 몇 번인지 세면 될 것 같아요", guide=talk[:1]),
                              {"guide.judge": ["[check]N2"], "guide.lead": ["같은 이름이 두 번 나오면 그 수는 어떻게 될까요?"]})
        self.assertEqual(fakes.tasks(fake), ["guide.judge", "guide.lead"])  # 내용 있는 말에만 모델이 답한다
        lead = fakes.prompt(fake, "guide.lead")
        self.assertIn("사용자에게 주장의 근거를 묻는 질문은 하지 않는다", lead)
        self.assertIn("맞는 부분과 빠진 부분", lead)
        self.assertIn(CONCEPT_FIRST, lead)
        from ..common.talk_rules import drop_echo
        self.assertEqual(drop_echo("다만 지금은 큐에서 무엇을 먼저 꺼낼까요?"), "지금은 큐에서 무엇을 먼저 꺼낼까요?")
        self.assertNotIn("근거를 묻는다.", lead)
        coded = fakes.planned([replace(fakes.hinted()[0], reference="from collections import deque\nbelt = deque()",
                                       hints=["덱은 `from collections import deque`로 가져와요. 무엇을 담을까요?"]), fakes.hinted()[1]])
        start = fakes.go(fakes.make_state("turn", fakes.context(plan=coded, open_count=1), mode="guide", event="start"), {})[0]
        self.assertEqual(start["result"]["reply"], coded.blocks[0].hints[0])  # 저장 힌트는 다시 검사하지 않는다(4차 확인: import 줄이 '참고 코드'에 걸렸다)
        done, fake = fakes.go(self.guide("count[p] += 1"), {"guide.judge": ["[check]Y g"]})
        self.assertEqual((done["result"]["move"], done["result"]["advance"], fakes.tasks(fake)), ("blank", True, ["guide.judge"]))
        self.assertEqual(done["result"]["reply"], open_lead("guide", "loop") + fakes.HINTS2[0])  # 가이드는 블록 이름이 보여 종류 안내가 없다
        self.assertNotIn("근거 수준", fakes.prompt(fake, "guide.judge"))

    def code_turn(self, code, open_count=1):
        blocks = [fakes.block(1, "준비", "def solution(a):\n    count = {}  # 센다", checks=["이름별로 센다"]),
                  fakes.block(2, "세기", "    for x in a:\n        count[x] = count.get(x, 0) + 1\n    return count", "loop",
                              checks=["하나씩 돈다", "없던 이름은 0에서 시작한다"])]
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=open_count, guide=[fakes.service("빈칸?", open_count - 1)])
        return fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id=f"b{open_count}", code=code)

    def test_same_code_as_reference_passes_without_judge(self):
        """실행 없이 통과하는 길은 계획 코드와 글자 그대로 같을 때뿐이다(줄 끝 공백·빈 줄만 다름). 공백·주석·틀 줄만 달라도 실행한다
        (그 차이를 같다고 보던 길이 문자열 안의 차이, 남는 '}', 가운데의 import를 실행 없이 통과시켰다)."""
        seen = []
        check = lambda pid, code, quick=False: seen.append(code) or {"status": "passed", "cases": []}  # noqa: E731
        done, fake = fakes.go(self.code_turn("def solution(a):   \n\n    count = {}  # 센다"), {"guide.lead": ["이 빈칸에는 무엇이 들어갈까요?"]}, check)
        self.assertEqual((fakes.tasks(fake), done["open_count"], done["block_check"].verdict, seen), (["guide.lead"], 2, "Y", []))
        for n, code in enumerate(("def solution(a):\n  count  =  {}\n\n# 그릇", "count = {}", "    count = {}"), 1):
            done, fake = fakes.go(self.code_turn(code), {"guide.lead": ["이 빈칸에는 무엇이 들어갈까요?"]}, check)
            self.assertEqual((fakes.tasks(fake), done["open_count"], done["block_check"].verdict, len(seen)), (["guide.lead"], 2, "Y", n))

    def test_last_block_pass_ends_without_question(self):
        passed = lambda pid, code, quick=False: {"status": "passed", "cases": [{"kind": "accuracy", "status": "passed"}]}  # noqa: E731
        done, fake = fakes.go(self.code_turn("for x in a:\n    count[x] = count.get(x, 0) + 1\nreturn count", 2), {}, passed)
        self.assertEqual((fake.calls, done["result"]["move"], done["result"]["reply"]), ([], "done", ALL_FILLED))
        self.assertNotIn("?", done["result"]["reply"])
        # '이 블록 채우기'로 마지막 블록을 채우면 말이 없었다. 화면이 채운 코드(참고 코드 그대로)를 확인받으면 끝 안내가 나간다
        filled = self.code_turn("    for x in a:\n        count[x] = count.get(x, 0) + 1\n    return count", 2)
        done, fake = fakes.go(filled, {})  # 참고 코드와 글자 그대로 같다: 실행 없이
        self.assertEqual((fake.calls, done["result"]["move"], done["result"]["reply"]), ([], "done", ALL_FILLED))

    def test_wrong_code_aims_at_the_missed_check(self):
        done, fake = fakes.go(self.code_turn("for x in a:\n    count[x] += 1\nreturn count", 2),
                              {"guide.check_code": ["[check]N2"], "guide.lead": ["처음 보는 이름이면 어떻게 될까요?"]})
        lead = fakes.prompt(fake, "guide.lead")
        self.assertIn("해내지 못한 것: 없던 이름은 0에서 시작한다", lead)
        self.assertIn("질문을 한 것이 아니다", lead)
        self.assertIn("count[x] += 1", lead)
        self.assertEqual((done["result"]["reply"], done["block_check"].miss), (unrun_note("") + " " + UNRUN_NO + " 처음 보는 이름이면 어떻게 될까요?", 2))
        self.assertIn("신호를 1번부터 하나씩", fakes.prompt(fake, "guide.check_code"))


SORT_BLOCKS = [fakes.block(1, "정렬", "def solution(items):\n    order = sorted(items)", checks=["가벼운 것부터 놓는다"], hints=list(fakes.HINTS1)),
               fakes.block(2, "차이", "    return order[-1] - order[0]", "var_during", checks=["가장 큰 것과 작은 것의 차이"], hints=list(fakes.HINTS2))]
SORT_CASES = [([3, 1, 2], 2), ([5, 5], 0), ([9, 1, 4], 8)]
SORT_CASES_ARGS = [([items], want) for items, want in SORT_CASES]


def line_of(exc) -> int | None:
    """가짜 채점 함수가 알려 주는 오류의 줄(실제 채점기가 줄 때와 같은 뜻: 이어 붙인 프로그램의 1부터 센 줄)."""
    if isinstance(exc, SyntaxError):
        return exc.lineno
    line, tb = None, exc.__traceback__
    while tb is not None:
        line = tb.tb_lineno if tb.tb_frame.f_code.co_filename == "<string>" else line
        tb = tb.tb_next
    return line


def sort_check(seen: list):
    """가짜 채점 함수: 프로그램을 돌려 케이스를 맞춰 본다(서버 verify의 모양. 첫 케이스만 공개 예시). 블록 코드 확인은 quick=True(효율성 케이스 뺌)로 부른다."""
    def check(problem_id, code, quick=False):
        seen.append(code)
        space, cases = {}, []
        for n, (items, want) in enumerate(SORT_CASES, 1):
            case = {"id": str(n), "kind": "example" if n == 1 else "accuracy", "input": json.dumps([items]), "expected": str(want), "got": "", "error": ""}
            try:
                exec(code, space)
                case["got"] = str(space["solution"](list(items)))
                case["status"] = "passed" if case["got"] == str(want) else "failed"
            except Exception as exc:  # noqa: BLE001 - NameError 등은 실행 오류
                case.update(status="runtime_error", error=f"Traceback (most recent call last):\n{type(exc).__name__}: {exc}", line=line_of(exc))
            cases.append(case)
        return {"status": next((c["status"] for c in cases if c["status"] != "passed"), "passed"), "cases": cases, "compile": ""}
    return check


class RunCheckTest(unittest.TestCase):
    """블록 코드 확인을 실행으로 판정한다('items.sort()', 'return count' 같은 맞는 코드를 모델 판정이 거부했다)."""

    def turn(self, code):
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)])
        return fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code=code)

    def test_different_shape_that_runs_passes_without_model(self):
        seen = []
        done, fake = fakes.go(self.turn("order = list(items)\norder.sort()"), {}, sort_check(seen))
        self.assertEqual((fake.calls, done["block_check"].verdict, done["open_count"]), ([], "Y", 2))
        self.assertEqual(done["result"]["reply"], open_lead("guide", "var_during") + fakes.HINTS2[0])
        self.assertEqual(seen, ["def solution(items):\n    order = list(items)\n    order.sort()\n    return order[-1] - order[0]"])

    def test_wrong_answer_is_no_without_model(self):
        done, fake = fakes.go(self.turn("order = items"), {}, sort_check([]))
        self.assertEqual((fake.calls, done["block_check"].verdict, done["open_count"]), ([], "N", 1))
        # 고정 앞말 + 실행에서 본 것 한 줄(공개 예시) + 다음 저장 힌트. 확인 항목은 인용하지 않는다
        self.assertEqual(done["result"]["reply"], RETRY_LEAD + "뒤 블록을 튜터의 코드로 이어 돌리면 예시 `solution([3, 1, 2])`의 기대한 값은 2인데 -1이 나와요. " + NOT_JOINED + " " + fakes.HINTS1[1])
        self.assertNotIn("가벼운 것부터", done["result"]["reply"])

    def test_seen_line_tells_only_public_examples(self):
        """거부 말에 이유가 없었다. 공개 예시만 값을 말하고, 숨은 테스트는 틀렸다는 것과 오류 이름만. kind가 없으면 숨은 케이스다."""
        from ..turn.code_check import seen_line

        def case(kind, status, **extra):
            return {"id": "1", "input": "[[3, 8, 6, 5], 11]", "expected": "2", "got": "", "error": "", "status": status, **({"kind": kind} if kind else {}), **extra}

        error = "Traceback (most recent call last):\n  File \"/tmp/x/solution.py\", line 3\nNameError: name 'weights' is not defined"
        rows = [([case("accuracy", "failed", got="9"), case("example", "failed", got="3")], False, "예시 `solution([3, 8, 6, 5], 11)`의 기대한 값은 2인데 3이 나왔어요."),
                ([case("example", "failed", got="3")], True, "예시 1의 기대한 출력은 2인데 3이 나왔어요."),
                ([case("example", "passed"), case("accuracy", "failed", got="3")], False, "예시는 맞지만 숨은 테스트에서 틀렸어요."),
                ([case(None, "failed", got="3")], False, "예시는 맞지만 숨은 테스트에서 틀렸어요."),
                ([case("example", "timeout")], False, "끝나지 않거나 너무 오래 걸렸어요."),
                ([case("example", "runtime_error", error=error)], False, "`NameError: name 'weights' is not defined`가 났어요."),
                ([case("accuracy", "runtime_error", error=error)], False, "숨은 테스트에서 `NameError`가 났어요."),
                ([case("example", "failed", got="x" * 100)], False, f"예시 `solution([3, 8, 6, 5], 11)`의 기대한 값은 2인데 {'x' * 80}…가 나왔어요.")]
        for cases, program, want in rows:
            self.assertEqual(seen_line({"status": "failed", "cases": cases}, program), want)
        self.assertEqual(seen_line({"status": "compile_error", "cases": [], "compile": "/tmp/a/Main.java:5: error: cannot find symbol\n  symbol: variable x"}, True),
                         "`cannot find symbol: x`가 났어요.")  # 모은 파일의 줄 번호는 사용자가 볼 수 없다

    def test_name_error_finds_my_name_without_model(self):
        """'items.sort()'가 뒤 블록의 'order'와 어긋나 NameError → 모델이 거부했다. 뒤 블록의 'order'를 'items'로 바꿔 돌리면 통과한다."""
        seen = []
        done, fake = fakes.go(self.turn("items.sort()"), {}, sort_check(seen))
        self.assertEqual((fake.calls, done["block_check"].verdict, done["block_check"].renames), ([], "Y", [["items", "order"]]))
        self.assertEqual((len(seen), seen[-1].splitlines()[-1]), (1, "    return items[-1] - items[0]"))  # 짝 없는 헛실행 없이 처음부터 짝지어 돈다
        done, fake = fakes.go(self.turn("items.sort()"), {}, None)  # 채점 함수가 없으면 모델
        self.assertEqual(fakes.tasks(fake), ["guide.check_code"])

    def test_later_block_runs_with_my_earlier_code_and_names(self):
        """다른 블록은 사용자가 적어 통과한 코드로, 나머지 계획 코드는 이름 바꾸기 표를 적용해 잇는다. 풀리지 않는 없는 이름 오류는 모델 없이 N."""
        states = {"b1": BlockState("b1", "items.sort()", code_hash("items.sort()"), "Y", renames=[["items", "order"]])}
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], block_states=states)
        seen = []
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="return max(items) - min(items)"), {}, sort_check(seen))
        self.assertEqual((fake.calls, done["block_check"].verdict, done["renamed"]), ([], "Y", []))
        self.assertEqual(seen, ["def solution(items):\n    items.sort()\n    return max(items) - min(items)"])
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="    return items[-1] - items[0]"), {}, sort_check(seen))
        self.assertEqual((done["block_check"].verdict, len(seen)), ("Y", 1))  # 내 이름으로 채워 준 코드와 글자 그대로 같다: 실행 없이 통과
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="return arr[-1] - arr[0]"), {}, sort_check([]))
        self.assertEqual((fake.calls, done["block_check"].verdict), ([], "N"))  # 계획에 없는 없는 이름은 사용자 탓이다(모델로 넘기지 않는다)

    def test_frame_lines_typed_are_not_doubled(self):
        seen = []
        done, fake = fakes.go(self.turn("def solution(items):\n    order = list(items)\n    order.sort()"), {}, sort_check(seen))
        self.assertEqual((fake.calls, done["block_check"].verdict), ([], "Y"))
        self.assertEqual(seen[0].count("def solution"), 1)


    def test_renamed_code_passes_with_name_note(self):
        """'conveyor'로 통과한 뒤 채운 블록('belt')과 모으니 NameError였다. 이름만 달라 통과하면 이름 안내를 붙이고 본문에 싣는다."""
        from ..common.talk_rules import rename_note
        from ..save.respond import body_for

        seen = []
        done, fake = fakes.go(self.turn("arr = sorted(items)"), {}, sort_check(seen))
        note = "이 블록에서 쓴 이름(`arr`)을 튜터의 코드는 다른 이름(`order`)으로 불러요. 뒤 블록을 '이 블록 채우기'로 채우면 내 이름으로 바꿔 채워요."
        self.assertEqual((len(seen), done["block_check"].verdict, done["result"]["renamed"]), (1, "Y", [["arr", "order"]]))  # 이름이 달라 실행으로 통과
        self.assertEqual(rename_note([["arr", "order"]]), note)
        self.assertEqual(done["result"]["reply"], note + " " + open_lead("guide", "var_during") + fakes.HINTS2[0])
        body = body_for(done["request"], done["result"], done["ctx"])
        self.assertEqual(body["renamed"], [["arr", "order"]])
        chair = [fakes.service(fakes.HINTS1[0], 0), fakes.service(OPEN_LEAD + fakes.HINTS2[0], 1, "m2")]
        found = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=2, chair=chair)
        done, fake = fakes.go(fakes.make_state("turn", found, mode="chair", event="block_filled", block_id="b1", code="arr = sorted(items)"), {}, sort_check([]))
        self.assertEqual((fake.calls, done["result"]["reply"]), ([], FOUND_OK + " " + note))  # 통과 말 뒤에(실행으로 통과)
        from ..turn.pairs import pair_block
        info = pair_block("for x in a:\n    t += x", "for k in a:\n    t += k", {}, "print(t)", {"t"}, "python")
        self.assertEqual((info.open, info.guess()), ([], {}))  # 뒤 블록이 읽지 않는 이름은 짝이 필요 없다
        # 짝의 근거는 만드는 문장이다: 'n, k = map(…)'의 자리마다 같은 꼴이라 굳은 짝
        info = pair_block("day_count, window_size = map(int, input().split())\nfirst_line = 1", "n, k = map(int, input().split())", {},
                          "day_count window_size", set(), "python")
        self.assertEqual(info.fixed, {"day_count": "n", "window_size": "k"})
        self.assertIn("쓴 이름(`n`)을 튜터의 코드는 다른 이름(`belt`)으로", rename_note([["n", "belt"]]))
        states = {"b1": BlockState("b1", "arr = sorted(items)", code_hash("arr = sorted(items)"), "Y", renames=[["arr", "order"]])}
        again = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)], block_states=states)
        done, fake = fakes.go(fakes.make_state("turn", again, mode="guide", event="block_filled", block_id="b1", code="arr = sorted(items)  # 다시"), {}, sort_check([]))
        self.assertEqual((done["result"]["renamed"], done["block_check"].renames), ([], [["arr", "order"]]))  # 이미 알린 짝은 다시 알리지 않는다
        self.assertNotIn("`arr`", done["result"]["reply"])


def exec_check(seen: list, cases: list, timeout_if: str = ""):
    """가짜 채점 함수(sort_check와 같은 모양, 케이스를 받는다). 첫 케이스만 공개 예시. 코드에 timeout_if가 있으면 시간 초과로 본다."""
    def check(problem_id, code, quick=False):
        seen.append(code)
        rows = []
        for n, (args, want) in enumerate(cases, 1):
            case = {"id": str(n), "kind": "example" if n == 1 else "accuracy", "input": json.dumps(args), "expected": str(want), "got": "", "error": ""}
            if timeout_if and timeout_if in code:
                case["status"] = "timeout"
            else:
                try:
                    space = {}
                    exec(code, space)
                    case["got"] = str(space["solution"](*json.loads(json.dumps(args))))
                    case["status"] = "passed" if case["got"] == str(want) else "failed"
                except Exception as exc:  # noqa: BLE001
                    case.update(status="runtime_error", error=f"Traceback (most recent call last):\n{type(exc).__name__}: {exc}", line=line_of(exc))
            rows.append(case)
        return {"status": next((c["status"] for c in rows if c["status"] != "passed"), "passed"), "cases": rows, "compile": ""}
    return check


LOOP_BLOCKS = [fakes.block(1, "돌기", "def solution(items):\n    res = []\n    for x in items:", "loop", hints=list(fakes.HINTS1)),
               fakes.block(2, "담고 돌려주기", "        res.append(x)\n    return res", "var_during", hints=list(fakes.HINTS2))]


class BlockCheckResultTest(unittest.TestCase):
    """바깥 줄이 있는 블록의 들여쓰기, 틀린 까닭을 그 코드에서 말하기, 같은 코드 다시 확인, 오류 한 줄, 힌트 붙이기, 틀린 수."""

    def sort_turn(self, code, states=None):
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)], block_states=states or {})
        return fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code=code)

    def loop_turn(self, code):
        ctx = fakes.context(plan=fakes.planned(LOOP_BLOCKS), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)])
        return fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code=code)

    def test_outer_line_block_is_placed_and_flat_code_is_told(self):
        from ..turn.code_check import INDENT_NOTE

        check = exec_check([], [([[3, 1, 2]], [3, 1, 2]), ([[5]], [5])])
        for code in ("    res.append(x)\nreturn res", "        res.append(x)\n    return res", "  res.append(x)\nreturn res"):
            done, fake = fakes.go(self.loop_turn(code), {}, check)
            self.assertEqual((fake.calls, done["block_check"].verdict), ([], "Y"), code)
            self.assertEqual(done["block_check"].code, code)  # 첫 줄 들여쓰기를 남겨 저장한다
        done, fake = fakes.go(self.loop_turn("res.append(x)\nreturn res"), {}, check)  # 계획 코드를 평평하게: 빠른 길로 통과하지 않는다
        seen = "앞 블록을 튜터의 코드로 이어 돌리면 예시 `solution([3, 1, 2])`의 기대한 값은 [3, 1, 2]인데 [3]이 나와요. " + NOT_JOINED + " " + INDENT_NOTE  # 앞 블록이 계획 코드다
        self.assertEqual((fake.calls, done["block_check"].verdict, done["verdict"].seen), ([], "N", seen))
        self.assertEqual(done["result"]["reply"], RETRY_LEAD + seen)  # 들여쓰기 안내에는 저장 힌트를 붙이지 않는다

    def test_tried_name_tells_what_my_code_did(self):
        from ..turn.code_check import assumed, hold_name

        seen = []  # 튜터 이름(order)의 NameError가 아니라 내 이름(arr)으로 돌린 시도의 오답을 말한다
        done, fake = fakes.go(self.sort_turn("arr = list(items)"), {}, sort_check(seen))
        self.assertEqual((len(seen), done["verdict"].seen), (2, "뒤 블록을 튜터의 코드로 이어 돌리면 예시 `solution([3, 1, 2])`의 기대한 값은 2인데 -1이 나와요. " + NOT_JOINED))  # 실행 둘: 이은 것, 내 블록만 이은 것
        self.assertEqual(done["result"]["reply"], RETRY_LEAD + done["verdict"].seen + " " + fakes.HINTS1[1])  # 오답에는 저장 힌트를 붙인다
        seen = []  # 시간 초과면 시도 한 번에서 멈춘다(후보가 둘이어도)
        done, fake = fakes.go(self.sort_turn("arr = list(items)\nfoo = 1"), {}, exec_check(seen, SORT_CASES_ARGS, timeout_if="arr[-1]"))
        self.assertTrue(done["verdict"].unsure)
        self.assertEqual((len(seen), done["verdict"].seen, done["block_check"].verdict),
                         (2, "뒤 블록을 튜터의 코드로 이어 돌리면 끝나지 않거나 너무 오래 걸려요. " + assumed([["arr", "order"]], True), "N"))  # 끝나지 않아 다른 짝을 다 돌려 보지 못했다: 확인 전
        seen = []  # 어떤 시도도 이름을 풀지 못했다: 고칠 곳(그 이름)을 말하고 힌트는 붙이지 않는다
        stuck = lambda pid, code, quick=False: seen.append(code) or {"status": "runtime_error", "compile": "", "cases": [  # noqa: E731
            {"id": "1", "kind": "example", "input": "[[3, 1, 2]]", "expected": "2", "got": "", "status": "runtime_error",
             "error": "Traceback (most recent call last):\nNameError: name 'order' is not defined"}]}
        done, fake = fakes.go(self.sort_turn("arr = list(items)"), {}, stuck)
        need = hold_name(["order"])  # 계획 이름의 없는 이름 오류는 내 코드 탓으로 말하지 않는다
        self.assertEqual((done["verdict"].seen, done["result"]["reply"], done["block_check"].verdict), (need, need, "N"))  # 확인 전: '아직 넘어가지 않아요'라 하지 않는다

    def test_unreadable_compile_error_tries_the_plan_name(self):
        """C++ 'using namespace std'에서 계획 이름 'end'가 std::end로 풀려 '없는 이름' 오류가 아니었다. 이 블록이 대입한 계획 이름을 내 이름으로 바꿔 본다."""
        seen = []
        check = lambda pid, code, quick=False: seen.append(code) or (  # noqa: E731
            {"status": "compile_error", "cases": [], "compile": "solution.cpp:21:23: error: reference to overloaded function could not be resolved"}
            if "order" in code else {"status": "passed", "cases": [], "compile": ""})
        done, fake = fakes.go(self.sort_turn("arr = list(items)\narr.sort()"), {}, check)
        self.assertEqual((fake.calls, done["block_check"].verdict, done["block_check"].renames, len(seen)), ([], "Y", [["arr", "order"]], 1))  # 처음부터 짝지어 돈다

    def test_same_wrong_code_runs_again_and_counts(self):
        code = "order = items"
        first, _ = fakes.go(self.sort_turn(code), {}, sort_check([]))
        seen = []
        again, fake = fakes.go(self.sort_turn(code + "  ", {"b1": first["block_check"]}), {}, sort_check(seen))
        self.assertEqual((len(seen), again["verdict"].seen, again["block_check"].tries), (2, first["verdict"].seen, 2))  # 다시 돌려(이은 것, 내 블록만 이은 것) 까닭을 말한다. 또 낸 N도 센다
        passed = BlockState("b1", "order = sorted(items)", code_hash("order = sorted(items)"), "Y", tries=3)
        done, _ = fakes.go(self.sort_turn("order = sorted(items)", {"b1": passed}), {}, sort_check([]))
        self.assertEqual(done["block_check"].tries, 3)  # 통과한 블록을 다시 확인해도 틀린 수(tries − 1)가 늘지 않는다

    def test_syntax_error_gets_no_saved_hint(self):
        done, fake = fakes.go(self.sort_turn("order = sorted(items"), {}, sort_check([]))
        self.assertEqual((done["block_check"].verdict, done["verdict"].hint), ("N", False))
        self.assertTrue(done["result"]["reply"].startswith(RETRY_LEAD + "내 블록 1번째 줄(`order = sorted(items`)에서 실행 오류가 났어요.\n`SyntaxError"), done["result"]["reply"])
        self.assertNotIn(fakes.HINTS1[1], done["result"]["reply"])

    def test_error_row_is_tidied(self):
        from ..turn.code_check import _error_row

        self.assertEqual(_error_row("/tmp/x/Main.java:14: error: cannot find symbol\n        int days = pay.length();\n  symbol:   method length()", True),
                         "cannot find symbol: length")
        self.assertEqual(_error_row("solution.cpp:21:23: error: reference to overloaded function could not be resolved", True),
                         "reference to overloaded function could not be resolved")
        self.assertEqual(_error_row("Traceback (most recent call last):\nAttributeError: 'list' object has no attribute 'sorted'. Did you mean: 'sort'?"),
                         "AttributeError: 'list' object has no attribute 'sorted'")
        long = "UnboundLocalError: cannot access local variable 'boxes' where it is not associated with a value at all here"
        self.assertEqual(_error_row(long), "UnboundLocalError: cannot access local variable 'boxes' where it is not…")  # 낱말 경계에서 자른다

    def test_fill_uses_my_names(self):
        """내 이름(conveyor)으로 통과한 뒤 채운 블록에 계획 이름(belt)이 들어왔다."""
        from ..common.solution import same_code, swap_names

        blocks = [fakes.block(1, "줄", "def solution(a):\n    belt = []"), fakes.block(2, "올리기", "    belt += [a]", hints=list(fakes.HINTS2)),
                  fakes.block(3, "답", "    return belt", hints=list(fakes.HINTS1))]
        states = {"b1": BlockState("b1", "conveyor = []", code_hash("conveyor = []"), "Y", renames=[["conveyor", "belt"]])}
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=3, block_states=states, guide=[fakes.service(fakes.HINTS1[0], 2)])
        filled = {}
        for block_id in ("b2", "b3"):
            done, fake = fakes.go(fakes.make_state("fill", ctx, block_id=block_id), {})
            filled[block_id] = done["result"]["code"]
            self.assertEqual(fake.calls, [])
        self.assertEqual(filled, {"b2": "conveyor += [a]", "b3": "return conveyor"})  # 블록 칸은 알맹이를 맨 앞에 둔다(들여쓰기는 이어 붙일 때 놓는다)
        self.assertFalse(same_code(filled["b2"], blocks[1].reference, "python"))  # 고쳐 쓰는 이름(+=)은 이름만 달라도 같은 코드가 아니다
        self.assertTrue(same_code(filled["b2"], swap_names(blocks[1].reference, {"belt": "conveyor"}, "python"), "python"))  # 이 자리의 표로 바꾼 계획 코드와는 같다
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b3", code=filled["b3"]), {},
                              exec_check([], [([7], [7])]))  # 대입하지 않는 블록은 이름 바꾸기 표로 돌려 통과한다
        self.assertEqual((fake.calls, done["block_check"].verdict), ([], "Y"))


HASH2 = [fakes.block(1, "세기", "def solution(rented, returned):\n    count = {}\n    for name in rented:\n        count[name] = count.get(name, 0) + 1", "loop", hints=list(fakes.HINTS1)),
         fakes.block(2, "종류 수", "    kinds = len(count)", "var_during", hints=list(fakes.HINTS1)),
         fakes.block(3, "그릇", "    answer = []", "var_during", hints=list(fakes.HINTS1)),
         fakes.block(4, "빼기", "    for name in returned:\n        count[name] -= 1", "loop", hints=list(fakes.HINTS1)),
         fakes.block(5, "마지막 하나", "        if count[name] == 0:\n            kinds -= 1", "condition", hints=list(fakes.HINTS1)),
         fakes.block(6, "담기", "        answer.append(kinds)\n    return answer", "var_during", hints=list(fakes.HINTS1))]
HASH2_CASES = [([["tent", "lamp", "chair", "chair", "stove"], ["chair", "tent", "stove"]], [4, 3, 2]),
               ([["mat", "mat", "mat", "axe"], ["mat", "axe", "mat", "mat"]], [2, 1, 1, 0])]


def passed_block(block_id, code, pairs=()):
    return BlockState(block_id, code, code_hash(code), "Y", renames=[list(pair) for pair in pairs])


class BlockCheckPairingTest(unittest.TestCase):
    """이름 짝을 블록 자리마다의 표로, 오류를 기다리지 않고 먼저 짝짓는다. 채점 함수는 가짜(받은 프로그램을 돌린다)."""

    MINE = {"b1": passed_block("b1", "cnt = {}\nfor r in rented:\n    cnt[r] = cnt.get(r, 0) + 1", [("cnt", "count"), ("r", "name")]),
            "b2": passed_block("b2", "left = len(cnt)", [("left", "kinds")])}

    def turn(self, blocks, states, block_id, code, cases=None):
        index = [b.id for b in blocks].index(block_id)
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=index + 1, guide=[fakes.service(fakes.HINTS1[0], index)], block_states=states)
        seen = []
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id=block_id, code=code), {},
                              exec_check(seen, cases or HASH2_CASES) if not callable(cases) else cases(seen))
        self.assertEqual(fake.calls, [])
        return done, seen

    def test_reused_plan_name_gets_a_pair_per_block(self):
        """블록 1을 cnt/r로 통과(계획 count/name). 블록 4(계획 'for name in returned:')를 내 반복 변수로 적으면 가짜 오답이었다."""
        for code, pair in (("for g in returned:\n    cnt[g] -= 1", [["g", "name"]]),
                           ("for r in returned:\n    cnt[r] -= 1", []),  # 같은 이름을 다시 씀: 이 자리의 표로 채운 코드와 같다(짝 r → name이 이어진다)
                           ("for idx in range(len(returned)):\n    g = returned[idx]\n    cnt[g] -= 1", [["g", "name"]])):
            done, seen = self.turn(HASH2, self.MINE, "b4", code)
            self.assertEqual((done["block_check"].verdict, done["block_check"].renames), ("Y", pair), (code, done["verdict"].seen))
        # 블록 1을 채우기로 채웠다(계획 이름 name이 살아 있다): Python은 끝난 반복의 변수가 남아 오류 없이 오답이 나던 경우
        done, seen = self.turn(HASH2, {}, "b4", "for g in returned:\n    count[g] -= 1")
        self.assertEqual((done["block_check"].verdict, done["block_check"].renames), ("Y", [["g", "name"]]))
        states = {"b4": done["block_check"]}  # 그 짝으로 블록 5를 돌리면 끝난 반복의 name이 아니라 g를 쓴다
        done, seen = self.turn(HASH2, states, "b5", "if count[g] == 0:\n    kinds = kinds - 1")
        self.assertEqual(done["block_check"].verdict, "Y", done["verdict"].seen)
        self.assertIn("        answer.append(kinds)", seen[0])

    def test_fill_uses_the_table_of_its_place(self):
        """채우기: 블록 5를 채울 때 블록 4의 짝이 블록 1의 같은 계획 이름 짝을 덮는다. 계획 이름을 그대로 쓰면 예전 짝이 끝난다."""
        for code, pairs, want in (("for g in returned:\n    cnt[g] -= 1", [("g", "name")], "if cnt[g] == 0:\n    left -= 1"),
                                  ("for name in returned:\n    cnt[name] -= 1", [], "if cnt[name] == 0:\n    left -= 1")):
            states = {**self.MINE, "b4": passed_block("b4", code, pairs)}
            ctx = fakes.context(plan=fakes.planned(HASH2), open_count=5, block_states=states)
            done, fake = fakes.go(fakes.make_state("fill", ctx, block_id="b5"), {})
            self.assertEqual((done["result"]["code"], fake.calls), (want, []))
        ctx = fakes.context(plan=fakes.planned(HASH2), open_count=4, block_states=self.MINE)
        done, _ = fakes.go(fakes.make_state("fill", ctx, block_id="b4"), {})
        self.assertEqual(done["result"]["code"], "for r in returned:\n    cnt[r] -= 1")  # 블록 4 자리는 블록 1의 짝

    def test_my_compile_error_is_told_when_pairs_are_reliable(self):
        """'Math.maxx' + 내 이름 dp → NEED_NAME이 아니라 그 컴파일 오류를 말한다(짝의 수가 같다)."""
        error = "Main.java:3: error: cannot find symbol\n        int[] dp = new int[n];\n  symbol:   method maxx(int,int)\n  location: class Math"

        def check(seen):
            return lambda pid, code, quick=False: seen.append(code) or (
                {"status": "compile_error", "cases": [], "compile": error, "compile_line": next(n for n, row in enumerate(code.splitlines(), 1) if "maxx" in row)}
                if "maxx" in code else {"status": "passed", "cases": [], "compile": ""})

        done, seen = self.turn(SORT_BLOCKS, {}, "b1", "dp = sorted(items).maxx()", check)
        self.assertEqual((done["verdict"].seen, done["verdict"].hint, done["block_check"].verdict, len(seen)),
                         ("내 블록 1번째 줄(`dp = sorted(items).maxx()`)에서 컴파일 오류가 났어요.\n`cannot find symbol: maxx` " + NOT_JOINED, False, "N", 2))  # 내 블록의 줄에서 난 오류라 틀렸다고 말한다(실행 둘)
        self.assertIn("return dp[-1] - dp[0]", seen[0])  # 처음부터 짝지어 돌렸다

    def test_unreliable_pairs_ask_for_the_names(self):
        """'q[0]'을 바로 쓴 블록(내 이름 하나, 계획 이름 둘). 짝을 못 찾았다고 말하고(HOLD_NAME), 그 이름을 만들면 통과한다."""
        from ..turn.code_check import assumed, hold_name as need_name

        blocks = [fakes.block(1, "범위", "def solution(q):\n    start = q[0] * 10\n    high = q[1]", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    return start + high", hints=list(fakes.HINTS2))]
        cases = [([[1, 2]], 12), ([[3, 5]], 35)]
        done, _ = self.turn(blocks, {}, "b1", "s = q[0] * 10", cases)
        self.assertEqual((done["verdict"].seen, done["verdict"].hint), (need_name(["high"]), False))  # start는 만드는 문장이 같은 s와 굳었다
        done, _ = self.turn(blocks, {}, "b1", "s = q[0]\nhi = q[1]\nextra = 0", cases)  # hi는 굳고 start의 짝을 어느 시도로도 못 찾았다
        # start의 짝은 굳지 않았지만 첫 후보(s)로 이어 돌렸다 — 그 결과와 쓰인 가정을 말한다
        self.assertEqual((done["verdict"].seen, done["block_check"].verdict),  # 어림 짝을 다 돌려 보아 이어지지 않아요이고, 그 짝을 사실로 말한다
                         ("뒤 블록을 튜터의 코드로 이어 돌리면 예시 `solution([1, 2])`의 기대한 값은 12인데 3이 나와요. " + assumed([["s", "start"]]) + " " + NOT_JOINED, "N"))
        self.assertEqual(need_name(["high", "start"]), "튜터의 뒤 코드는 값을 `high`, `start` 이름으로 이어 써요. 내 코드에서 그 값이 어느 것인지 찾지 못해 이어 돌리지 못했어요. "
                         "그 이름으로 맞추거나, 맞다고 생각하면 '이대로 넘어가기'를 눌러요.")
        done, _ = self.turn(blocks, {}, "b1", "s = q[0] * 10\nhi = q[1]", cases)
        self.assertEqual((done["block_check"].verdict, done["block_check"].renames), ("Y", [["s", "start"], ["hi", "high"]]))

    def test_renamed_helper_function_passes(self):
        """도우미 함수 이름만 바꾼 블록(firstAtLeast → lowIdx)이 내 매개변수 이름 오류로 거부됐다."""
        from ..common.solution import defined_function

        blocks = [fakes.block(1, "도우미", "def first_at_least(values, x):\n    return len([v for v in values if v < x])", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "def solution(prices, x):\n    return first_at_least(sorted(prices), x)", hints=list(fakes.HINTS2))]
        done, seen = self.turn(blocks, {}, "b1", "def low_idx(v, x):\n    return len([a for a in v if a < x])", [([[3, 1, 2], 2], 1)])
        self.assertEqual((done["block_check"].verdict, done["block_check"].renames, len(seen)), ("Y", [["low_idx", "first_at_least"]], 1))
        cpp = "int lowIdx(const vector<int>& v, int x) { return lower_bound(v.begin(), v.end(), x) - v.begin(); }"
        self.assertEqual([defined_function(c, "cpp") for c in (cpp, "for (auto& q : ranges) {\n    int s = 0;", "} else if (a) {")], ["lowIdx", "", ""])

    def test_five_qa_passes_still_pass(self):
        """예전에도 통과하던 꼴: 'lo, hi = …'/'count = 0'(이름만 다름)."""
        blocks = [fakes.block(1, "양 끝", "def solution(items):\n    lo, hi = 0, len(items) - 1\n    boxes = 0", hints=list(fakes.HINTS1)),
                  fakes.block(2, "세기", "    while lo <= hi:\n        boxes += 1\n        lo += 1\n    return boxes", "loop", hints=list(fakes.HINTS2))]
        done, seen = self.turn(blocks, {}, "b1", "lo, hi = 0, len(items) - 1\ncount = 0", [([[1, 2, 3]], 3)])
        self.assertEqual((done["block_check"].verdict, done["block_check"].renames, len(seen)), ("Y", [["count", "boxes"]], 1))  # 실행으로 통과

    def test_program_and_value_lines(self):
        """표준 입출력 문제는 몇 번째 예시인지와 기대·나온 출력을, 나온 값은 기대한 값과 같은 꼴로 말한다."""
        from ..turn.code_check import seen_line

        def case(n, got, kind="example"):
            return {"id": str(n), "kind": kind, "input": "[[1]]", "expected": "[3, 2, 0]", "got": got, "status": "failed" if n == 2 else "passed"}

        self.assertEqual(seen_line({"cases": [case(1, ""), case(2, "[1,0,0]")]}, False), "예시 `solution([1])`의 기대한 값은 [3, 2, 0]인데 [1, 0, 0]이 나왔어요.")
        self.assertEqual(seen_line({"cases": [case(1, ""), case(2, "7\n")]}, True), "예시 2의 기대한 출력은 [3, 2, 0]인데 7이 나왔어요.")
        self.assertEqual(seen_line({"cases": [case(1, ""), case(2, "")]}, True), "예시 2의 기대한 출력은 [3, 2, 0]인데 아무것도 나오지 않았어요.")


class BlockCheckNewNameTest(unittest.TestCase):
    """새로 만드는 이름(초기값 없는 선언·매개변수·꼴·타입), open은 처음 만드는 이름만, 확실한 짝, 겹치지 않는 모든 나눔, HOLD_NAME."""

    turn = BlockCheckPairingTest.turn

    def test_created_names_kind_and_type(self):
        from ..common.solution import created_names

        self.assertEqual(created_names("def first_at_least(values, x):\n    left = 0\n    for i, (a, b) in enumerate(values):\n        left += 1", "python"),
                         [("values", "param", ""), ("x", "param", ""), ("left", "var", ""), ("i", "loop", ""), ("a", "loop", ""), ("b", "loop", "")])
        self.assertEqual(created_names("StringBuilder sb;\nint[] arr = new int[n];\nst = new StringTokenizer(br.readLine());\nreturn sb;", "java"),
                         [("sb", "var", "StringBuilder"), ("arr", "var", "int[]")])
        self.assertEqual(created_names("int lowIdx(const vector<int>& v, int x) {\n    vector<int> res;\n    int lo = 0, hi = v.size();\n"
                                       "    for (auto& q : ranges) {\n        cin >> lo;", "cpp"),
                         [("v", "param", "vector<int>"), ("x", "param", "int"), ("res", "var", "vector<int>"), ("lo", "var", "int"), ("hi", "var", "int"),
                          ("q", "loop", "")])

    def test_missing_update_line_is_told_by_its_run(self):
        """앞 블록에서 만든 이름을 고쳐 쓰는 줄(boxes += 1)을 빠뜨린 코드는 그 실행의 오답으로 말한다(이름 안내가 아니다)."""
        from ..turn.code_check import assumed

        blocks = [fakes.block(1, "양 끝", "def solution(items):\n    lo, hi = 0, len(items) - 1\n    boxes = 0", hints=list(fakes.HINTS1)),
                  fakes.block(2, "세기", "    while lo <= hi:\n        boxes += 1\n        hi -= 1", "loop", hints=list(fakes.HINTS2)),
                  fakes.block(3, "답", "    return boxes", hints=list(fakes.HINTS1))]
        states = {"b1": passed_block("b1", "lo, hi = 0, len(items) - 1\ncount = 0", [("count", "boxes")])}
        done, seen = self.turn(blocks, states, "b2", "while lo <= hi:\n    hi -= 1", [([[1, 2, 3]], 3)])
        # 그대로 쓴 lo가 count와 꼴이 같아(= 0) 무리다 — 다른 차례도 돌려 보고, 첫 가정의 결과와 쓰인 가정을 말한다
        self.assertEqual((done["verdict"].seen, len(seen), done["block_check"].verdict),
                         ("뒤 블록을 튜터의 코드로 이어 돌리면 예시 `solution([1, 2, 3])`의 기대한 값은 3인데 0이 나와요. " + assumed([["count", "boxes"]]) + " " + NOT_JOINED, 3, "N"))  # 실행 셋: 첫 가정, 다른 차례, 내 블록만. 짝을 다 돌려 보았으니 이어지지 않아요다

    def test_types_and_pairings(self):
        """타입이 다른 후보는 시도하지 않는다. 두 이름을 함께 바꿔야 하는 짝에 닿는다."""
        blocks = [fakes.block(1, "준비", "int solution(vector<int> a) {\n    int total = 0;\n    string label = \"\";", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    return total + label.size();\n}", hints=list(fakes.HINTS2))]

        def check(seen):
            return lambda pid, code, quick=False: seen.append(code) or {"status": "failed", "compile": "", "cases": [
                {"id": str(len(seen)), "kind": "example", "input": "[[1]]", "expected": "1", "got": str(len(seen)), "status": "failed"}]}

        ctx = fakes.context(plan=fakes.planned(blocks), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)], language="cpp")
        seen = []
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="int t = 0;\nauto s = 1;\nint u = 2;"), {}, check(seen))
        self.assertTrue(seen and not any("t.size()" in program or "u.size()" in program for program in seen), seen)  # string 자리에 int 이름을 넣지 않는다
        self.assertTrue(done["verdict"].seen.startswith("뒤 블록을 튜터의 코드로 이어 돌리면 ") and "이렇게 알고 이어 돌렸어요" in done["verdict"].seen, done["verdict"].seen)  # 굳지 않은 짝으로 돌린 결과 + 그 가정
        blocks = [fakes.block(1, "범위", "def solution(ranges):\n    for low, high in ranges:\n        start = low * 10", "loop", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "        return start + high", hints=list(fakes.HINTS2))]
        done, seen = self.turn(blocks, {}, "b1", "for q in ranges:\n    a, b = q\n    s = a * 10", [([[[1, 2]]], 12), ([[[3, 5]]], 35)])
        self.assertEqual((done["block_check"].verdict, sorted(done["block_check"].renames)), ("Y", [["b", "high"], ["s", "start"]]), done["verdict"].seen)

    def test_try_seconds_and_same_failure(self):
        """6초가 지나면 새 시도를 하지 않는다(시계를 넣어서). 모든 시도가 같은 실패면 그 실패(짝과 상관없다), 확실한 짝 + 내 코드의 오류면 그 오류."""
        from unittest.mock import patch

        from ..turn import code_check
        from ..turn.code_check import GUESSED_CUT, assumed

        blocks = [fakes.block(1, "범위", "def solution(q):\n    start = q[0] * 10\n    high = q[1]", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    return start + high", hints=list(fakes.HINTS2))]
        ticks = iter([0, 7, 7, 7, 7, 7])
        with patch.object(code_check, "now", lambda: next(ticks)):
            done, seen = self.turn(blocks, {}, "b1", "s = q[0]\nhi = q[1]\nextra = 0", [([[1, 2]], 12)])
        self.assertEqual(len(seen), 2)  # 새 시도는 하지 않는다: 이은 것 하나, 내 블록만 이은 것 하나
        self.assertTrue(done["verdict"].unsure and GUESSED_CUT in done["verdict"].seen and NOT_JOINED not in done["verdict"].seen, done["verdict"].seen)  # 짝을 다 돌려 보지 못했다: 확인 전
        broken = lambda seen: lambda pid, code, quick=False: seen.append(code) or {"status": "runtime_error", "compile": "", "cases": [  # noqa: E731
            {"id": "1", "kind": "example", "input": "[[1, 2]]", "expected": "12", "got": "", "status": "runtime_error", "error": "ZeroDivisionError: division by zero",
             "line": next(n for n, row in enumerate(code.splitlines(), 1) if "// 0" in row)}]}
        done, seen = self.turn(blocks, {}, "b1", "s = q[0] // 0\nhi = q[1]\nextra = 0", broken)
        self.assertEqual((done["verdict"].seen, done["block_check"].verdict, len(seen) > 1),  # 어림 짝을 다 돌려 보고 모두 실패했다: 이어지지 않아요(난 곳을 말한다)
                         ("내 블록 1번째 줄(`s = q[0] // 0`)에서 실행 오류가 났어요.\n`ZeroDivisionError: division by zero` " + assumed([["s", "start"]]) + " " + NOT_JOINED, "N", True))
        done, seen = self.turn(blocks, {}, "b1", "s = q[0] // 0\nhi = q[1]", broken)  # 확실한 짝: 첫 시도가 내 코드의 일이다
        self.assertEqual((done["verdict"].seen, done["block_check"].verdict), ("내 블록 1번째 줄(`s = q[0] // 0`)에서 실행 오류가 났어요.\n`ZeroDivisionError: division by zero` " + NOT_JOINED, "N"))
        self.assertIn("return s + hi", seen[0])


GREEDY = [fakes.block(1, "정렬", "def solution(items, capacity):\n    weights = sorted(items)", hints=list(fakes.HINTS1)),
          fakes.block(2, "양 끝", "    light = 0\n    heavy = len(weights) - 1\n    boxes = 0", "var_during", hints=list(fakes.HINTS1)),
          fakes.block(3, "돌기", "    while light <= heavy:", "loop", hints=list(fakes.HINTS1)),
          fakes.block(4, "같이 담기", "        if light < heavy and weights[light] + weights[heavy] <= capacity:\n            light += 1", "condition", hints=list(fakes.HINTS1)),
          fakes.block(5, "상자", "        heavy -= 1\n        boxes += 1", hints=list(fakes.HINTS1)),
          fakes.block(6, "답", "    return boxes", hints=list(fakes.HINTS1))]
GREEDY_CASES = [([[3, 8, 6, 5], 11], 2), ([[7, 7, 7], 13], 3), ([[1, 2], 2], 2)]


class BlockCheckEntryAndGroupTest(unittest.TestCase):
    """진입 함수 줄, 만드는 문장으로 짓는 짝·바꿔도 되는 무리·뒤에서 다시 고르기, 새 이름에 담기, 매개변수 차례, 고쳐 쓰는 이름."""

    turn = BlockCheckPairingTest.turn

    def walk(self, blocks, steps, cases):
        """블록을 차례로 확인한다(채우기는 'fill'). 저장 길처럼 판정 기록과 다시 고른 앞 블록 기록을 남긴다."""
        states, out = {}, []
        for k, code in steps:
            block_id = f"b{k}"
            if code == "fill":
                ctx = fakes.context(plan=fakes.planned(blocks), open_count=k, block_states=dict(states))
                done, _ = fakes.go(fakes.make_state("fill", ctx, block_id=block_id), {}, exec_check([], cases))
                states[block_id] = done["block_check"]
                out.append(done)
                continue
            done, seen = self.turn(blocks, dict(states), block_id, code, cases)
            states[block_id] = done["block_check"]
            for fix in done.get("block_fixes") or []:
                states[fix.block_id] = fix
            out.append(done)
        return out, states

    def test_entry_line_after_comment_is_head(self):
        """주석 뒤의 진입 함수 줄이 머리말이다. 알맹이만 적은 블록 1을 이어도 그 줄이 있다(Python, Go)."""
        from ..common.solution import frame_of, spliced

        py = ["# 재귀 대신 스택으로 돈다\n# 두 줄 주석\ndef solution(parent, files, limit):\n    n = len(parent)", "    return n"]
        self.assertEqual(frame_of(py[0], "python")["head"][-1], "def solution(parent, files, limit):")
        self.assertIn("def solution(parent, files, limit):\n    sz = len(parent)", spliced(py, 0, "sz = len(parent)", "python"))
        go = ["package main\n\n// 주석 한 줄\nfunc solution(parent []int, files []int, limit int) int {\n\tn := len(parent)", "\treturn n\n}"]
        program = spliced(go, 0, "sz := len(parent)", "go")
        self.assertIn("func solution(parent []int, files []int, limit int) int {\n\tsz := len(parent)", program)  # 탭 들여쓰기도 탭으로
        self.assertEqual(spliced(go, 0, "package main\n\n// 내 주석\nfunc solution(parent []int, files []int, limit int) int {\n\tsz := len(parent)", "go").count("func solution"), 1)

    def test_entry_missing_is_not_my_fault(self):
        """이어 붙이기가 진입 함수를 잃으면 모델로 넘기지 않고 '확인하지 못했다'는 고정 말로 끝낸다(진행·힌트 없음)."""
        from ..common.talk_rules import CANNOT_RUN

        missing = lambda seen: lambda pid, code, quick=False: seen.append(code) or {"status": "entry_missing", "cases": [], "compile": ""}  # noqa: E731
        done, seen = self.turn(SORT_BLOCKS, {}, "b1", "order = list(items)\norder.sort()", missing)
        self.assertEqual((done["result"]["reply"], done["block_check"].verdict, done["open_count"]), (CANNOT_RUN, "N", 1))  # 내 블록 탓이 아니라 확인 전이다(기록은 N이고 틀린 수에 넣지 않는다)

    def test_reordered_declarations_are_not_announced_and_rechosen_later(self):
        """'n = 0', 'j = len(w) - 1', 'i = 0'(계획은 light, heavy, boxes). heavy만 굳은 짝으로 알리고, 0끼리의 무리는 알리지 않고 뒤 블록에서 다시 고른다."""
        steps = [(1, "def solution(items, capacity):\n    w = sorted(items)"), (2, "n = 0\nj = len(w) - 1\ni = 0"), (3, "while i <= j:"),
                 (4, "if i < j and w[i] + w[j] <= capacity:\n    i += 1"), (5, "fill"), (6, "fill")]
        out, states = self.walk(GREEDY, steps, GREEDY_CASES)
        self.assertEqual([d["block_check"].verdict for d in out], ["Y"] * 6)
        self.assertEqual(out[1]["renamed"], [["j", "heavy"]])  # 무리(n, i ↔ light, boxes)는 알리지 않는다
        self.assertEqual(sorted(states["b2"].renames), [["i", "light"], ["j", "heavy"], ["n", "boxes"]])  # 블록 3이 다시 골랐다
        self.assertEqual(out[4]["result"]["code"], "j -= 1\nn += 1")  # 채우기도 다시 고른 표로

    def test_filled_text_is_kept_as_is(self):
        """채운 블록은 채운 글 그대로 통과한 블록 상태로 남고(틀린 수는 그대로), 뒤 확인의 이어 붙이기에 그 글이 쓰인다."""
        states = {"b1": BlockState("b1", "x = 1", code_hash("x = 1"), "N", tries=2)}
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, block_states=states)
        done, _ = fakes.go(fakes.make_state("fill", ctx, block_id="b1"), {}, exec_check([], SORT_CASES_ARGS))
        record = done["block_check"]
        self.assertEqual((record.verdict, record.code, record.tries - (record.verdict == "Y")), ("Y", "order = sorted(items)", 2))  # 블록 칸에는 알맹이만(진입 함수 머리는 이어 붙일 때 틀이 넣는다)
        done, seen = self.turn(SORT_BLOCKS, {"b1": record}, "b2", "return max(order) - min(order)", SORT_CASES_ARGS)
        self.assertIn("    order = sorted(items)\n    return max(order) - min(order)", seen[0])

    def test_sorted_into_new_name(self):
        """'ps = sorted(prices)'(계획은 'prices = sorted(prices)')는 통과하고 짝 [ps, prices]를 알린다."""
        blocks = [fakes.block(1, "준비", "def solution(prices, x):\n    prices = sorted(prices)\n    answer = []", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    answer.append(prices[0] + x)\n    return answer", hints=list(fakes.HINTS2))]
        done, _ = self.turn(blocks, {}, "b1", "ps = sorted(prices)\nres = []", [([[3, 1, 2], 10], [11])])
        self.assertEqual((done["block_check"].verdict, sorted(done["result"]["renamed"])), ("Y", [["ps", "prices"], ["res", "answer"]]))

    def test_param_order_is_told(self):
        """도우미 함수의 매개변수 차례를 바꾸면 내 탓의 오류가 아니라 뒤 블록이 부르는 차례를 알린다."""
        from ..turn.code_check import hold_name

        blocks = [fakes.block(1, "도우미", "def lower(values, x):\n    return len([v for v in values if v < x])", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "def solution(prices, x):\n    return lower(sorted(prices), x)", hints=list(fakes.HINTS2))]
        done, _ = self.turn(blocks, {}, "b1", "def lower(x, values):\n    return len([v for v in values if v < x])", [([[3, 1, 2], 2], 1)])
        self.assertEqual((done["verdict"].seen, done["verdict"].hint), (hold_name(["values", "x"], params=True), False))

    def test_when_my_fault(self):
        """(가) 갱신을 빠뜨림 → 그 실행의 오답, (나) 짝이 모두 굳음 → 내 코드의 오류, (다) 모든 가정이 같은 실패 → 그 실패. 그 밖에는 HOLD_NAME."""
        states = {"b1": passed_block("b1", "def solution(items, capacity):\n    w = sorted(items)", [("w", "weights")]),
                  "b2": passed_block("b2", "lo, hi = 0, len(w) - 1\ncount = 0", [("lo", "light"), ("hi", "heavy"), ("count", "boxes")]),
                  "b3": passed_block("b3", "while lo <= hi:"), "b4": passed_block("b4", "if lo < hi and w[lo] + w[hi] <= capacity:\n    lo += 1")}
        done, _ = self.turn(GREEDY, states, "b5", "hi -= 1\ncoutn += 1", GREEDY_CASES)  # (다) 무리의 두 차례 모두 같은 오류
        self.assertIn("coutn", done["verdict"].seen)
        blocks = [fakes.block(1, "범위", "def solution(q):\n    start = q[0] * 10\n    high = q[1]", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    return start + high", hints=list(fakes.HINTS2))]
        done, _ = self.turn(blocks, {}, "b1", "s = q[0]\nhi = q[1]\nextra = 0", [([[1, 2]], 12)])  # start의 짝이 굳지 않고 가정마다 실패가 다르다
        self.assertTrue(done["verdict"].seen.startswith("뒤 블록을 튜터의 코드로 이어 돌리면 ") and "이렇게 알고 이어 돌렸어요" in done["verdict"].seen, done["verdict"].seen)
        done, _ = self.turn(SORT_BLOCKS, {}, "b1", "arr = sorted(items[1:])", SORT_CASES_ARGS)  # (나) 굳은 짝(만드는 꼴 하나뿐)
        self.assertEqual(done["verdict"].seen, "뒤 블록을 튜터의 코드로 이어 돌리면 예시 `solution([3, 1, 2])`의 기대한 값은 2인데 1이 나와요. " + NOT_JOINED)

    def test_rewritten_name_is_not_new(self):
        """'coutn += 1'은 'boxes += 1'과 같은 코드가 아니다(새로 만드는 이름만 이름이 달라도 같다)."""
        from ..common.solution import same_code

        self.assertFalse(same_code("hi -= 1\ncoutn += 1", "    hi -= 1\n    count += 1", "python"))
        self.assertTrue(same_code("arr = sorted(items)", "    order = sorted(items)", "python"))


BS4 = [fakes.block(1, "도우미", "def cnt_le(n, m, area):\n    c = 0", hints=list(fakes.HINTS1)),
       fakes.block(2, "세기", "    for i in range(1, n + 1):\n        c += min(m, area // i)\n    return c", "loop", hints=list(fakes.HINTS1)),
       fakes.block(3, "범위", "def solution(n, m, k):\n    lo, hi = 1, n * m", hints=list(fakes.HINTS1)),
       fakes.block(4, "찾기", "    while lo < hi:\n        mid = (lo + hi) // 2\n        if cnt_le(n, m, mid) >= k:\n            hi = mid\n        else:\n"
                              "            lo = mid + 1\n    return lo", "loop", hints=list(fakes.HINTS1))]
BS4_CASES = [([2, 3, 4], 3), ([3, 3, 5], 3), ([4, 2, 1], 1)]
TP4 = [fakes.block(1, "준비", "def solution(profits, target):\n    seen = {0: 1}", hints=list(fakes.HINTS1)),
       fakes.block(2, "세기 준비", "    count = 0\n    total = 0", "var_during", hints=list(fakes.HINTS1)),
       fakes.block(3, "돌기", "    for p in profits:\n        total += p\n        count += seen.get(total - target, 0)\n        seen[total] = seen.get(total, 0) + 1", "loop",
                   hints=list(fakes.HINTS1)),
       fakes.block(4, "답", "    return count", hints=list(fakes.HINTS1))]
TP4_CASES = [([[3, -2, 4, -1, 2], 5], 2), ([[1, 1, 1], 2], 2)]
SUM3 = [fakes.block(1, "준비", "def solution(n):\n    total = 0", hints=list(fakes.HINTS1)),
        fakes.block(2, "더하기", "    for i in range(1, n + 1):\n        total += i", "loop", hints=list(fakes.HINTS2)),
        fakes.block(3, "답", "    return total", hints=list(fakes.HINTS1))]


class BlockCheckInvariantTest(unittest.TestCase):
    """불변 조건(통과는 실행이 뒷받침, 모으기는 한 곳, 앞 블록이 바뀌면 뒤 통과를 물림, 말은 한 일 그대로)과 어림 손보기."""

    turn = BlockCheckPairingTest.turn
    walk = BlockCheckEntryAndGroupTest.walk

    def again(self, blocks, states, block_id, code, cases, open_count):
        """앞 블록 다시 확인(진행 위치 open_count는 그대로)."""
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=open_count, guide=[fakes.service(fakes.HINTS1[0], open_count - 1)], block_states=states)
        seen = []
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id=block_id, code=code), {}, exec_check(seen, cases))
        self.assertEqual(fake.calls, [])
        return done, seen

    def test_only_same_text_passes_without_run(self):
        """매개변수 자리를 바꿔 정의한 도우미(계획 이름 그대로)는 자리 번호로 같다고 보아 실행 없이 통과하던 길이 없다. 표로 바꾼 계획 코드와 글자가 같을 때만 실행 없이."""
        done, seen = self.turn(BS4, {}, "b1", "def cnt_le(area, n, m):\n    c = 0", BS4_CASES)
        self.assertTrue(seen and done["verdict"].unsure, (seen, done["verdict"].seen))  # 매개변수 차례가 다르다: 이어 돌려 확인하지 못했다
        done, seen = self.turn(BS4, {}, "b1", "def cnt_le(n, m, area):\n    c = 0", BS4_CASES)
        self.assertEqual((seen, done["block_check"].verdict), ([], "Y"))
        done, seen = self.turn(BS4, {}, "b1", "def cnt_le(n, m, area):\n    c = 0  # 그대로", BS4_CASES)  # 주석만 달라도 실행한다
        self.assertEqual((len(seen), done["block_check"].verdict), (1, "Y"))
        # 이름을 모두 바꾼 매개변수는 자리로 짐작한 짝이다: 틀린 코드면 HOLD_PARAMS가 아니라 돌린 결과와 그 가정
        done, seen = self.turn(BS4, {}, "b1", "def cnt_le(rows, cols, x):\n    c = 1", BS4_CASES)
        self.assertTrue(done["verdict"].seen.startswith("뒤 블록을 튜터의 코드로 이어 돌리면 예시") and "`rows`→`n`, `cols`→`m`, `x`→`area`" in done["verdict"].seen,
                        done["verdict"].seen)

    def test_changed_block_stales_later_and_failed_recheck_is_unchecked(self):
        """통과한 블록의 이름만 바꿔 다시 확인하면 뒤 블록(저장된 글 그대로 잇는다)의 옛 이름 때문에 통과하지 못하고, 그 블록은 '확인 전'(?)·틀린 수 그대로,
        뒤의 통과한 블록도 '확인 전'으로 돌아간다(글과 진행은 그대로)."""
        steps = [(1, "def solution(n):\n    acc = 0"), (2, "for i in range(1, n + 1):\n    acc += i"), (3, "return acc")]
        out, states = self.walk(SUM3, steps, [([3], 6), ([1], 1)])
        self.assertEqual([d["block_check"].verdict for d in out], ["Y"] * 3)
        done, seen = self.again(SUM3, states, "b1", "def solution(n):\n    res = 0", [([3], 6), ([1], 1)], 3)
        self.assertIn("    for i in range(1, n + 1):\n        acc += i", seen[0])  # 뒤 블록은 저장된 글 그대로
        self.assertEqual((done["block_check"].verdict, done["block_check"].tries, done["open_count"]), ("?", states["b1"].tries, 3))
        self.assertTrue(done["verdict"].seen.startswith("내 코드만으로 돌렸더니 내 2번 블록 2번째 줄(`acc += i`)에서 실행 오류가 났어요."), done["verdict"].seen)  # 뒤 블록이 모두 내 글: 오류는 그 블록의 줄에서 난다
        self.assertIn("`UnboundLocalError", done["verdict"].seen)
        self.assertEqual(sorted((f.block_id, f.verdict, f.code) for f in done["block_fixes"]),
                         [("b2", "?", states["b2"].code), ("b3", "?", states["b3"].code)])

    def test_lead_assumption_while_and_fill_note(self):
        """for 블록을 while로 적고 증가를 다음 블록에 두면 앞말 + 시간 초과 + while 문장(저장 힌트 없음).
        채우기: 표로 바꾼 글이 통과하지 못하면 계획 이름으로 채우고 알린다(확인 전)."""
        from ..fill.nodes import FILL_NOTE
        from ..turn.code_check import WHILE_NOTE

        states = {"b1": passed_block("b1", "def solution(n):\n    total = 0")}
        ctx = fakes.context(plan=fakes.planned(SUM3), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], block_states=states)
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="i = 1\nwhile i <= n:\n    total += i"), {},
                           exec_check([], [([3], 6)], timeout_if="while"))
        self.assertEqual((done["verdict"].seen, done["verdict"].hint), ("뒤 블록을 튜터의 코드로 이어 돌리면 끝나지 않거나 너무 오래 걸려요. " + NOT_JOINED + " " + WHILE_NOTE, False))  # 끝까지 돌지 못하는 이음은 이어지지 않아요다
        self.assertEqual((done["block_check"].verdict, done["verdict"].unsure, done["block_check"].tries), ("N", False, 1))  # 넘어가지 못한 횟수로 센다
        self.assertNotIn(fakes.HINTS2[1], done["result"]["reply"])
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="i = 1\nwhile i <= n:\n    total += 10 // (i - 1)"), {},
                           exec_check([], [([3], 6)]))  # 시간 초과가 아닌 실패도 계획이 for로 연 자리면 while 문장
        self.assertTrue(done["verdict"].seen.endswith("ZeroDivisionError: integer division or modulo by zero` " + NOT_JOINED + " " + WHILE_NOTE), done["verdict"].seen)
        states = {"b1": passed_block("b1", "def solution(n):\n    acc = 0\n    t = 5", [("acc", "total")]),  # 짝(acc)이 뜻과 다르다(t가 답)
                  "b2": passed_block("b2", "for i in range(1, n + 1):\n    t += i")}
        ctx = fakes.context(plan=fakes.planned(SUM3), open_count=3, block_states=states)
        done, fake = fakes.go(fakes.make_state("fill", ctx, block_id="b3"), {}, exec_check([], [([3], 6)]))
        self.assertEqual((done["result"]["code"], done["result"]["note"], done["block_check"].verdict, fake.calls),
                         ("return total", FILL_NOTE.format(names="`total`"), "?", []))
        states["b2"] = passed_block("b2", "for i in range(1, n + 1):\n    acc += i")
        ctx = fakes.context(plan=fakes.planned(SUM3), open_count=3, block_states=states)
        done, _ = fakes.go(fakes.make_state("fill", ctx, block_id="b3"), {}, exec_check([], [([3], 6), ([4], 10)]))
        self.assertEqual((done["result"]["code"], "note" in done["result"], done["block_check"].verdict), ("return acc", False, "Y"))  # 통과하면 표로 바꾼 글
        from ..fill.nodes import FILL_GUESS  # 굳지 않은 무리의 첫 가정으로 바꿔 채웠으면 그 짐작을 알린다(굳은 짝 j는 넣지 않는다)
        out, _ = self.walk(GREEDY, [(1, "def solution(items, capacity):\n    w = sorted(items)"), (2, "n = 0\nj = len(w) - 1\ni = 0"), (3, "fill")], GREEDY_CASES)
        self.assertEqual((out[2]["result"]["code"], out[2]["result"]["note"]), ("while n <= j:", FILL_GUESS.format(mine="`n`", plan="`light`", each="")))

    def test_compose_is_the_checked_program(self):
        """머리 줄(def)을 블록 2에 적어도 모은 글과 블록 확인이 돌린 프로그램이 같고, 머리 줄은 한 번만 바깥에 있다."""
        from ..common.solution import composed_parts

        steps = [(1, "acc = 0"), (2, "def solution(n):\n    for i in range(1, n + 1):\n        acc += i"), (3, "return acc")]
        out, states = self.walk(SUM3, steps, [([3], 6), ([1], 1)])
        self.assertEqual([d["block_check"].verdict for d in out], ["Y"] * 3, [d["verdict"].seen for d in out])
        parts = composed_parts(SUM3, {f"b{k}": {"code": code} for k, code in steps}, "python")
        self.assertEqual("\n".join(row for _, part in parts for row in part.split("\n") if "# 블록" not in row),
                         "def solution(n):\n    acc = 0\n    for i in range(1, n + 1):\n        acc += i\n    return acc")

    def test_helper_names_live_inside_the_helper(self):
        """도우미의 매개변수 짝(n → rows)은 그 함수가 끝나면 표에서 빠진다. solution 블록을 계획 그대로 적으면 통과하고, 채우기는 계획의 머리줄."""
        steps = [(1, "def cnt_le(rows, cols, x):\n    c = 0"), (2, "for i in range(1, rows + 1):\n    c += min(cols, x // i)\nreturn c"),
                 (3, "def solution(n, m, k):\n    lo, hi = 1, n * m")]
        out, states = self.walk(BS4, steps, BS4_CASES)
        self.assertEqual([d["block_check"].verdict for d in out], ["Y"] * 3, [d["verdict"].seen for d in out])
        ctx = fakes.context(plan=fakes.planned(BS4), open_count=3, block_states={k: v for k, v in states.items() if k != "b3"})
        done, _ = fakes.go(fakes.make_state("fill", ctx, block_id="b3"), {}, exec_check([], BS4_CASES))
        self.assertEqual(done["result"]["code"], "lo, hi = 1, n * m")  # 블록 칸에는 알맹이만(진입 함수 머리는 틀이 넣는다)
        from ..common.solution import scoped_names  # 함수의 끝은 다음 블록 맨 앞의 빈 줄·주석이 아니라 마지막 코드 줄(heap_5: 도우미 매개변수 left가 solution의 left를 바꿨다)
        self.assertEqual(scoped_names(["def f(a):\n    b = a\n", "\n# 답\ndef solution(a):\n    return f(a)"], "python"), [(0, {"a", "b"})])

    def test_plan_name_in_a_group_is_not_settled(self):
        """계획의 total을 내 답 변수로, sum을 누적 합으로. 블록 2는 짝을 알리지 않고, 블록 3에서 다른 차례로 다시 골라 통과한다."""
        steps = [(1, "def solution(profits, target):\n    seen = {0: 1}"), (2, "total = 0\nsum = 0"),
                 (3, "for p in profits:\n    sum += p\n    total += seen.get(sum - target, 0)\n    seen[sum] = seen.get(sum, 0) + 1")]
        out, states = self.walk(TP4, steps, TP4_CASES)
        self.assertEqual([d["block_check"].verdict for d in out], ["Y"] * 3, [d["verdict"].seen for d in out])
        self.assertEqual(out[1]["result"].get("renamed") or [], [])  # 굳지 않은 무리는 알리지 않는다
        self.assertEqual(sorted(states["b2"].renames), [["sum", "total"], ["total", "count"]])  # 블록 3이 다시 고른 차례

    def test_no_new_trial_that_would_pass_the_limit(self):
        """새 시도는 '지난 시간 + 방금 실행에 걸린 시간'이 한도 안일 때만 시작한다."""
        from unittest.mock import patch

        from ..turn import code_check

        blocks = [fakes.block(1, "범위", "def solution(q):\n    start = q[0] * 10\n    high = q[1]", hints=list(fakes.HINTS1)),
                  fakes.block(2, "답", "    return start + high", hints=list(fakes.HINTS2))]
        ticks = iter([0, 0, 4, 4, 4, 4, 4, 4])  # 시작 0, 첫 실행 0→4초: 4 + 4 > 6이라 두 번째 시도를 하지 않는다
        with patch.object(code_check, "now", lambda: next(ticks, 4)):
            _, seen = self.turn(blocks, {}, "b1", "s = q[0]\nhi = q[1]\nextra = 0", [([[1, 2]], 12)])
        self.assertEqual(len(seen), 2)  # 이은 것 하나(새 시도는 없다), 내 블록만 이은 것 하나

    def test_small_feedback_words_and_quiet_fill(self):
        """제출 상태는 한국어 말로, 블록 코드 확인의 실패는 '틀린 코드' 한 줄로만. 마지막 블록 채우기의 확인은 '나'의 말로 넣지 않는다."""
        from ..common.talk_rules import RETRY_LEAD
        from ..feedback.prompts import record_lines
        from ..save.nodes import collect

        guide = [fakes.service(fakes.HINTS1[0], 0), fakes.user("x = 1", 0, "u1"), fakes.service(RETRY_LEAD + "`NameError`가 났어요.", 0, "m2", "run")]
        ctx = fakes.context(plan=fakes.planned(fakes.two()), open_count=2, guide=guide, block_states={"b1": BlockState("b1", "x = 2", "h", "Y", None, 2)},
                            failed_submissions=["runtime_error", "failed", "timeout"])
        lines = record_lines(ctx, ctx.plan)
        self.assertFalse(any("넘어가지 못한 답" in line for line in lines), lines)
        self.assertIn("- 블록 1(입력받기) 블록 코드 확인에서 튜터의 코드와 이어지지 않은 횟수 1번(틀렸다는 뜻이 아니다)", lines)
        self.assertIn("- 통과하지 못한 제출: 실행 오류 1번, 오답 1번, 시간 초과 1번", lines)
        for quiet, rows in ((False, 1), (True, 0)):
            state = fakes.make_state("turn", fakes.context(plan=fakes.planned(fakes.two()), open_count=2), mode="guide", event="block_filled",
                                     block_id="b2", code="print(1)", quiet=quiet)
            self.assertEqual(sum(row["role"] == "user" for row in collect({**state, "result": {"reply": "통과예요."}})["changes"]["messages"]), rows)


JAVA_LOOP = ["import java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n"
             "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        int n = Integer.parseInt(br.readLine().trim());\n        long sum = 0;",
             "        for (int i = 0; i < n; i++) {\n            sum += i;",
             "        }\n        System.out.println(sum);\n    }\n}"]


class BlockCheckHoldNameTest(unittest.TestCase):
    """이름 안내는 한 번에 다 말하고, 앞 블록에서 미리 만든 이름도 짝 후보로 보며, 이름 맞추기 실패는 틀린 수에 넣지 않고,
    앞 블록을 고쳐 뒤 블록의 통과를 물리면 그 수를 말한다."""

    turn = BlockCheckPairingTest.turn
    BLOCKS = [fakes.block(1, "벨트", "def solution(xs):\n    belt = []", hints=list(fakes.HINTS1)),
              fakes.block(2, "상태", "    load = 0\n    time = 0\n    nxt = 0", hints=list(fakes.HINTS2)),
              fakes.block(3, "답", "    for x in xs:\n        load += x\n        time += 1\n        belt.append(x)\n    return load * 10 + time + len(belt) * 0 + nxt", "loop", hints=list(fakes.HINTS1))]
    CASES = [([[1, 2]], 32), ([[5]], 51)]

    def test_hold_names_all_and_early_name_pairs(self):
        from ..turn.code_check import hold_name

        done, _ = self.turn(self.BLOCKS, {}, "b1", "belt = []", self.CASES)
        b1 = done["block_check"]
        done, _ = self.turn(self.BLOCKS, {"b1": b1}, "b2", "now = 0\nnxt = 0", self.CASES)  # time의 짝(now)은 어림뿐이다: load와 함께 한 번에
        self.assertEqual((done["verdict"].seen, done["block_check"].verdict, done["block_check"].tries), (hold_name(["load", "time"]), "N", 0))  # 확인 전: 틀린 수에 넣지 않는다
        done, _ = self.turn(self.BLOCKS, {"b1": b1}, "b1", "belt = []\nweight = 0", self.CASES)  # 블록 1에서 무게 합을 미리 만들었다
        early = done["block_check"]
        done, _ = self.turn(self.BLOCKS, {"b1": early}, "b2", "now = 0\nnxt = 0", self.CASES)
        self.assertEqual((done["block_check"].verdict, done["block_check"].renames), ("Y", [["weight", "load"], ["now", "time"]]))

    def test_failed_later_block_is_joined_as_plan_code(self):
        """넘어가지 못한(N) 뒤 블록의 저장된 글은 잇지 않는다(계획 코드로 잇는다): 맞게 고친 앞 블록이 그 탓에 넘어가지 못하지 않는다."""
        b1 = BlockState("b1", "belt = []", code_hash("belt = []"), "Y")
        b2 = BlockState("b2", "load = 0\ntime = 0\nnxt = 0", code_hash("load = 0\ntime = 0\nnxt = 0"), "Y")
        bad = "for x in xs:\n    load += x\nreturn -1"
        b3 = BlockState("b3", bad, code_hash(bad), "N")
        ctx = fakes.context(plan=fakes.planned(self.BLOCKS), open_count=3, guide=[fakes.service(fakes.HINTS1[0], 2)], block_states={"b1": b1, "b2": b2, "b3": b3})
        seen = []
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="belt = list()"), {}, exec_check(seen, self.CASES))
        self.assertEqual((done["block_check"].verdict, any("return -1" in code for code in seen)), ("Y", False))
        self.assertEqual([fix.block_id for fix in done.get("block_fixes") or []], ["b2"])  # 통과한 b2만 확인 전으로 물리고 b3은 N 그대로

    def test_withdrawn_blocks_are_counted_in_reply(self):
        from ..common.talk_rules import WITHDRAWN

        b1 = BlockState("b1", "belt = []", code_hash("belt = []"), "Y")
        b2 = BlockState("b2", "load = 0\ntime = 0\nnxt = 0", code_hash("load = 0\ntime = 0\nnxt = 0"), "Y")
        ctx = fakes.context(plan=fakes.planned(self.BLOCKS), open_count=3, guide=[fakes.service(fakes.HINTS1[0], 2)], block_states={"b1": b1, "b2": b2})
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="belt = list()"), {}, exec_check([], self.CASES))
        self.assertEqual(done["result"]["withdrawn"], ["b2"])
        self.assertTrue(done["result"]["reply"].endswith(WITHDRAWN.format(n=1)))
        # 이미 확인 전이던 뒤 블록도 센다(화면의 '확인 전' 칸 수와 같게). 물린 것이 없으면 말하지 않는다
        b3 = BlockState("b3", "for x in xs:", code_hash("for x in xs:"), "Y")
        ctx = replace(ctx, open_count=3, block_states={"b1": b1, "b2": replace(b2, verdict="?"), "b3": b3})
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="belt = list()"), {}, exec_check([], self.CASES))
        self.assertEqual((done["result"]["withdrawn"], done["result"]["reply"].endswith(WITHDRAWN.format(n=2))), (["b2", "b3"], True))
        ctx = replace(ctx, block_states={"b1": b1, "b2": replace(b2, verdict="?")})
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="belt = list()"), {}, exec_check([], self.CASES))
        self.assertNotIn("withdrawn", done["result"])


class ConceptReplyTest(unittest.TestCase):
    """5차 실제 모델 확인: 가이드가 '왜 덱을 써야 하나요?'에 답한 초안이 '3문장 초과, 뒤 블록 이름'(이름 '먼저 내리기')으로 대체 질문이 됐다."""

    TEXT = "상자는 줄의 순서대로 벨트에 오릅니다. 먼저 오른 상자가 먼저 나갑니다. 벨트에 오른 상자는 정확히 travel초 뒤에 벨트 끝에서 내립니다."
    DRAFT = ("덱을 쓰는 까닭은 먼저 오른 상자가 먼저 내리기 때문입니다. 벨트 위에 상자가 여러 개 있어도 매초 가장 먼저 내릴 상자는 가장 일찍 오른 상자 하나뿐입니다. "
             "그래서 오른 순서대로 줄을 세워 두면 앞에서 바로 꺼낼 수 있습니다. "
             "그러면 이 블록에서는 문제 글의 '벨트에 오른 상자는 정확히 travel초 뒤에 벨트 끝에서 내립니다'를 보면, 벨트 위 상자를 어떤 순서로 담아 둘까요?")

    def test_guide_answer_is_trimmed_not_replaced(self):
        blocks = [fakes.block(1, "벨트 줄 준비", "from collections import deque\nbelt = deque()", hints=list(fakes.HINTS1)),
                  fakes.block(2, "상태 값 준비", "load = 0"), fakes.block(3, "1초씩 반복", "while t:", "loop"), fakes.block(4, "먼저 내리기", "belt.popleft()", "loop")]
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=1, problem_text=self.TEXT, guide=[fakes.service(fakes.HINTS1[0], 0, move="blank")])
        state = fakes.make_state("turn", ctx, mode="guide", event="message", text="왜 덱을 써야 하나요?")
        done, fake = fakes.go(state, {"guide.judge": ["[check]N1"], "guide.lead": [self.DRAFT]})
        self.assertEqual(done["result"]["reply"], " ".join(sentences(self.DRAFT)[-3:]))  # 대체 질문이 아니라 답 + 질문(뒤 세 문장)
        self.assertEqual(reply_problems(self.DRAFT, move="blank", problem=self.TEXT, later_names=["먼저 내리기"]), ["3문장 초과", "뒤 블록 이름"])  # 의자 등은 그대로
        self.assertIn("뒤 블록 이름", reply_problems("상태 값 준비를 먼저 볼까요?", move="blank", problem=self.TEXT, later_names=["상태 값 준비"], loose_names=True))


class BraceCheckTest(unittest.TestCase):
    """계획은 반복을 다음 블록까지 열어 두는데 '}'로 닫아 적은 블록이 통과했고, 모은 코드는 컴파일 오류였다.
    실행을 먼저 하고(진입 줄 꼴이 다른 맞는 코드를 실행 전에 막았다), 컴파일·문법 오류가 나면 괄호 수 안내를 덧붙인다."""

    def turn(self, code):
        blocks = [fakes.block(1, "읽기", JAVA_LOOP[0]), fakes.block(2, "더하기", JAVA_LOOP[1], "loop", hints=list(fakes.HINTS2)), fakes.block(3, "출력", JAVA_LOOP[2], hints=list(fakes.HINTS1))]
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], language="java", mode="program")
        return fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code=code)

    def test_closed_loop_that_the_plan_keeps_open(self):
        seen = []

        def check(pid, code, quick=False):  # 괄호 짝이 맞지 않으면 컴파일 오류(채점기를 흉내 낸다)
            seen.append(code)
            if code.count("{") != code.count("}"):  # 남는 '}'는 끝 줄(튜터가 닫는 곳)에서 난다
                return {"status": "compile_error", "compile": "Main.java:12: error: class, interface, enum, or record expected", "cases": [], "compile_line": len(code.splitlines())}
            done = "System.out.println(sum)" in code  # 출력까지 이은 프로그램만 맞다
            return {"status": "passed" if done else "failed", "cases": [{"kind": "accuracy", "status": "passed" if done else "failed", "expected": "1", "got": ""}]}
        done, fake = fakes.go(self.turn("for (int i = 0; i < n; i++) {\n    sum += i;\n}"), {}, check)
        self.assertEqual((fake.calls, len(seen), done["block_check"].verdict), ([], 1, "N"))  # 오류는 튜터가 닫는 줄에서 났다: 내 블록 탓이라 할 수 없다(앞 블록에 글이 없어 내 블록만 잇는 실행은 하지 않는다)
        self.assertTrue(BRACE_OPEN in done["verdict"].seen and "class, interface" in done["verdict"].seen and "튜터의 코드" in done["verdict"].seen, done["verdict"].seen)
        done, fake = fakes.go(self.turn("for (int i = 0; i < n; i++) {\n    sum = sum + i;"), {}, check)
        self.assertEqual((fake.calls, done["block_check"].verdict, len(seen)), ([], "Y", 2))
        self.assertIn("        for (int i = 0; i < n; i++) {\n            sum = sum + i;\n        }\n        System.out.println(sum);", seen[1])
        done, fake = fakes.go(self.turn("for (int i = 0; i < n; i++) sum += i;"), {}, check)  # 중괄호 없는 한 줄 반복도 열어 두지 않았다
        self.assertIn(BRACE_OPEN, done["verdict"].seen)
        # 진입 줄 꼴이 계획과 다르면(화살표 함수) 실행 전에 '닫아 주세요'로 거부했다: 이제 실행한 결과를 말하고, 진입 줄에 기댄 괄호 수 안내는 붙이지 않는다
        arrow = [fakes.block(1, "준비", "function solution(n) {\n    let total = 0;"), fakes.block(2, "끝", "    return total + n;\n}")]
        ctx = fakes.context(plan=fakes.planned(arrow), open_count=1, guide=[fakes.service("빈칸?", 0)], language="javascript")
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1",
                                               code="const solution = (n) => {\n    let total = 0;"), {"guide.lead": ["다음은 무엇일까요?"]}, check)
        self.assertEqual(len(seen), 5)  # 앞의 셋이 실행 3번(앞 블록에 글이 없어 내 블록만 잇는 실행은 없다), 화살표 함수도 실행하고(이은 것 하나, 내 블록만 이은 것 하나) 말한다
        self.assertNotIn("괄호", done["verdict"].seen)
        self.assertEqual(brace_note("if (n > 0) {\n    sum += n;", fakes.block(9, "x", "        if (n > 0) sum += n;", "condition"), "java", True), BRACE_CLOSE)


KOTLIN_BLOCKS = [fakes.block(1, "세기 준비", "fun solution(heights: IntArray, limit: Int): Int {\n    var count = 0", hints=list(fakes.HINTS1)),
                 fakes.block(2, "세기", "    for (h in heights) {\n        if (h > limit) count++\n    }", "loop", hints=list(fakes.HINTS2)),
                 fakes.block(3, "돌려주기", "    return count\n}", "var_during", hints=list(fakes.HINTS2))]
KOTLIN_CODE = "\n".join(b.reference for b in KOTLIN_BLOCKS)


class HonestCheckTest(unittest.TestCase):
    """실행으로 뒷받침하지 못한 판정은 그렇다고 말한다: 검증되지 않은 풀이와는 이어 돌리지 않고, 실행하지 못한 통과·예시로만 본 통과는 그 말을 붙이며,
    문항의 방식은 넘겨받는다(Python이 아닌 함수 방식, 표준 입출력 방식의 문제 글로)."""

    def kotlin(self, code, block_id="b1", states=None, verified=True, check=None, scripts=None):
        """verified: True(검증된 풀이 가이드), False(예시를 통과하지 못함), "unrun"(채점하지 못해 확인하지 못함), None(가이드를 만들지 못해 없음).
        code가 None이면 '이 블록 채우기'."""
        guide = None if verified is None else Solution("세어 돌려준다.", ["센다"], KOTLIN_CODE, None if verified == "unrun" else verified)
        ctx = fakes.context(problem_text=fakes.KOTLIN_PROBLEM, language="kotlin", plan=fakes.planned(KOTLIN_BLOCKS), open_count=int(block_id[1:]),
                            guide=[fakes.service("빈칸?", int(block_id[1:]) - 1)], block_states=states or {}, solution=guide, canonical=guide)
        state = (fakes.make_state("fill", ctx, guide=False, block_id=block_id) if code is None else
                 fakes.make_state("turn", ctx, guide=False, mode="guide", event="block_filled", block_id=block_id, code=code))
        return fakes.go(state, scripts or {}, check)

    def test_no_guide_is_treated_like_an_unverified_one(self):
        """가이드를 만드는 모델 호출이 실패해 가이드가 없는 계획: 그 계획 코드와 이어 돌린 결과도, 글자가 같다는 것도 통과의 근거가 아니다."""
        seen = []
        check = lambda pid, code, quick=False: seen.append(code) or {"status": "passed" if "return count" in code and "count++" in code else "failed",  # noqa: E731
                                                                   "cases": [{"kind": "accuracy", "status": "passed"}]}  # 끝까지 쓴 프로그램만 통과한다
        for code in ("fun solution(heights: IntArray, limit: Int): Int {\n    var total = 0", KOTLIN_BLOCKS[0].reference):
            seen.clear()
            done, fake = self.kotlin(code, verified=None, check=check)
            self.assertEqual((fake.calls, done["block_check"].verdict, done["result"]["reply"].startswith(UNVERIFIED), done["open_count"]), ([], "?", True, 2))
            self.assertEqual(len(seen), 1)  # 튜터의 코드와 이은 프로그램은 돌리지 않고, 내 블록만 이은 것을 한 번 돌린다
            self.assertNotIn("count++", seen[0])
        seen.clear()
        done, fake = self.kotlin(KOTLIN_BLOCKS[0].reference, verified=True, check=check)  # 검증된 가이드가 있으면 그대로 통과한다
        self.assertEqual((seen, done["block_check"].verdict), ([], "Y"))

    def test_fill_says_what_it_could_not_run(self):
        """채운 코드를 실행으로 확인하지 못했으면 '확인 전'(?)으로 두고 그렇게 말한다: 채점 함수가 없을 때, 채점하지 못했을 때, 가이드를 믿을 수 없을 때."""
        from ..fill.nodes import FILL_REFUSED

        seen = []
        passed = lambda pid, code, quick=False: seen.append(code) or {"status": "passed", "cases": [{"kind": "accuracy", "status": "passed"}] * 2}  # noqa: E731
        done, fake = self.kotlin(None, "b2", check=passed)
        self.assertEqual((done["block_check"].verdict, "note" in done["result"], len(seen)), ("Y", False, 1))  # 실행으로 통과했다
        done, fake = self.kotlin(None, "b2")
        self.assertEqual(done["block_check"].verdict, "?")
        self.assertIn("확인 전이에요", done["result"]["note"])
        for status, why in (("toolchain_missing", "이 기기에 이 언어를 실행할 도구가 없어요"), ("no_cases", "이 문제에 돌려 볼 케이스가 없어요"), ("unknown_status", "이 코드를 돌리지 못했어요")):
            done, fake = self.kotlin(None, "b2", check=lambda pid, code, quick=False, status=status: {"status": status, "cases": []})
            self.assertEqual((done["block_check"].verdict, why in done["result"]["note"]), ("?", True), done["result"]["note"])
        for verified in (False, None):  # 가이드가 예시를 통과하지 못했거나 없다: 채우지 않고 그렇다고 말한다(없는 이름이나 빈 자리를 넣지 않는다. 돌리지도 않는다)
            seen.clear()
            done, fake = self.kotlin(None, "b2", verified=verified, check=passed)
            self.assertEqual((done["error"].code, done["error"].message, "block_check" in done, seen), ("fill_unavailable", FILL_REFUSED, False, []))
        mine = {"b1": BlockState("b1", "fun solution(heights: IntArray, limit: Int): Int {\n    var count = 0", "x", "Y"),
                "b3": BlockState("b3", "    return count\n}", "y", "Y")}
        done, fake = self.kotlin(None, "b2", states=mine, verified="unrun", check=passed)  # 다른 블록이 모두 내 코드면 계획 코드가 끼지 않는다: 돌린다
        self.assertEqual((done["block_check"].verdict, len(seen)), ("Y", 1))
        examples = lambda pid, code, quick=False: {"status": "passed", "cases": [{"kind": "example", "status": "passed"}] * 2}  # noqa: E731
        done, fake = self.kotlin(None, "b2", check=examples)
        self.assertEqual((done["block_check"].verdict, done["result"]["note"]), ("Y", EXAMPLES_ONLY))

    def test_unverified_plan_is_not_spliced(self):
        seen = []
        check = lambda pid, code, quick=False: seen.append(code) or {"status": "passed" if "return total" in code else "failed",  # noqa: E731
                                                                   "cases": [{"kind": "accuracy", "status": "passed"}]}  # 끝까지 쓴 프로그램만 통과한다
        done, fake = self.kotlin("fun solution(heights: IntArray, limit: Int): Int {\n    var total = 0", verified=False, check=check)
        self.assertEqual((fake.calls, len(seen), done["block_check"].verdict, done["block_check"].tries, done["result"]["reply"].startswith(UNVERIFIED), done["open_count"]),
                         ([], 1, "?", 1, True, 2))  # 모델로 넘기지 않고, 튜터의 코드와 이은 것은 돌리지 않고(내 블록만 이은 것 하나), '확인 전'으로 두고 넘어간다(틀린 수는 0)
        self.assertNotIn("count++", seen[0])
        seen.clear()
        done, fake = self.kotlin(KOTLIN_BLOCKS[0].reference, verified=False, check=check)  # 계획 코드와 글자가 같아도 검증되지 않은 코드라 통과의 근거가 아니다
        self.assertEqual((len(seen), done["block_check"].verdict, done["result"]["reply"].startswith(UNVERIFIED)), (1, "?", True))
        seen.clear()
        # 다른 블록이 모두 내 코드면 계획 코드가 끼지 않는다: 돌린다
        mine = {"b2": BlockState("b2", "for (h in heights) {\n    if (h > limit) total++\n}", "x", "Y"), "b3": BlockState("b3", "return total\n}", "y", "Y")}
        done, fake = self.kotlin("fun solution(heights: IntArray, limit: Int): Int {\n    var total = 0", states=mine, verified=False, check=check)
        self.assertEqual((len(seen), done["block_check"].verdict), (1, "Y"))
        self.assertIn("var total = 0\n    for (h in heights) {", seen[0])
        self.assertEqual(done["block_check"].tries, 1)

    def test_unrunnable_guide_is_not_called_a_failed_one(self):
        """풀이를 채점하지 못해 확인하지 못한 가이드(도구 없음 등)는 '예시를 통과하지 못했다'고 하지 않고, 실행하지 못한 판단의 말로 간다(까닭과 할 일)."""
        from ..fill.nodes import FILL_REFUSED

        for status, why in (("toolchain_missing", "이 기기에 이 언어를 실행할 도구가 없어요"), ("unsupported_signature", "이 문제의 인자 형은 아직 돌릴 수 없어요")):
            seen = []
            check = lambda pid, code, quick=False, status=status: seen.append(code) or {"status": status, "cases": []}  # noqa: E731
            for mine in ("fun solution(heights: IntArray, limit: Int): Int {\n    var total = 0", KOTLIN_BLOCKS[0].reference):  # 계획 코드와 같아도 실행 없이 통과시키지 않는다
                done, fake = self.kotlin(mine, verified="unrun", check=check, scripts={"guide.check_code": ["[check]Y"]})
                said = done["result"]["reply"]
                self.assertTrue(said.startswith(f"이 블록은 실행하지 못해서({why}) 코드를 읽고 본 판단이에요."), said)
                self.assertNotIn("예시", said)
                self.assertEqual((done["block_check"].verdict, done["open_count"], "설치하면" in said), ("?", 2, status == "toolchain_missing"))
            done, fake = self.kotlin("var total = 0", verified="unrun", check=check, scripts={"guide.check_code": ["[check]N1"], "guide.lead": ["어떻게 될까요?"]})
            self.assertTrue(done["result"]["reply"].startswith(f"이 블록은 실행하지 못해서({why})"), done["result"]["reply"])
            self.assertEqual((done["block_check"].verdict, done["block_check"].tries, done["open_count"]), ("N", 0, 1))  # 읽고 낸 거절: '확인 전'이고 넘기지 않지만 틀린 수에는 넣지 않는다
            done, fake = self.kotlin(None, "b2", verified="unrun", check=check)
            self.assertEqual(done["block_check"].verdict, "?")
            self.assertIn(why, done["result"]["note"])
            self.assertNotEqual(done["result"]["note"], FILL_REFUSED)
        # 그 사이 도구를 설치했다면 가이드를 지금 돌려 본다: 통과하면 믿고 이어 돌리고, 통과하지 못하면 예시를 통과하지 못한 가이드와 같다
        seen = []
        check = lambda pid, code, quick=False: seen.append(code) or {"status": "passed", "cases": [{"kind": "accuracy", "status": "passed"}]}  # noqa: E731
        done, fake = self.kotlin("var total = 0", verified="unrun", check=check)
        self.assertEqual((done["block_check"].verdict, len(seen), seen[0]), ("Y", 2, KOTLIN_CODE))  # 가이드를 한 번, 이어 붙인 프로그램을 한 번
        check = lambda pid, code, quick=False: {"status": "failed", "cases": [{"kind": "accuracy", "status": "failed"}]}  # noqa: E731
        done, fake = self.kotlin("var total = 0", verified="unrun", check=check)
        self.assertTrue(done["result"]["reply"].startswith(UNVERIFIED))

    def test_unrun_pass_is_said_and_shown_unchecked(self):
        from ..save.respond import body_for

        for status, why in (("toolchain_missing", "이 기기에 이 언어를 실행할 도구가 없어요"), ("unsupported_signature", "이 문제의 인자 형은 아직 돌릴 수 없어요")):
            check = lambda pid, code, quick=False, status=status: {"status": status, "cases": []}  # noqa: E731
            done, fake = self.kotlin("    var total = 0", check=check, scripts={"guide.check_code": ["[check]Y"]})
            said = done["result"]["reply"]
            self.assertTrue(said.startswith(f"이 블록은 실행하지 못해서({why}) 코드를 읽고 본 판단이에요."), said)
            self.assertEqual("설치하면" in said, status == "toolchain_missing")  # 사용자가 고칠 수 있는 까닭만 할 일을 말한다
            self.assertEqual((done["block_check"].verdict, done["open_count"], done["result"]["unsure"]), ("?", 2, True))  # '확인 전'으로 보이고 진행은 한다
            body = body_for(done["request"], done["result"], fakes.context(plan=fakes.planned(KOTLIN_BLOCKS), open_count=2))
            self.assertTrue(body["unsure"])

    def test_examples_only_pass_says_so(self):
        example = lambda pid, code, quick=False: {"status": "passed", "cases": [{"kind": "example", "status": "passed"}] * 2}  # noqa: E731
        done, fake = self.kotlin("    var total = 0", check=example)
        self.assertEqual((done["block_check"].verdict, fake.calls), ("Y", []))
        self.assertTrue(done["result"]["reply"].startswith(EXAMPLES_ONLY + " "), done["result"]["reply"])

    def test_program_mode_is_given_not_guessed(self):
        """def main이 없는 Python 표준 입출력 코드: 방식을 넘겨받아 '예시 N의 기대한 출력'으로 말한다(코드 모양으로 짐작하면 함수 호출 꼴로 말했다)."""
        blocks = [fakes.block(1, "읽기", "n = int(input())\nriders = list(map(int, input().split()))", hints=list(fakes.HINTS1)),
                  fakes.block(2, "고르기", "best = 0\nfor i in range(n):\n    if riders[i] > riders[best]:\n        best = i\nprint(best + 1)", "loop", hints=list(fakes.HINTS2))]
        failed = {"status": "failed", "cases": [{"kind": "example", "input": "3\n1 5 5\n", "expected": "2\n", "got": "3\n", "status": "failed"}]}
        code = "best = 0\nfor i in range(n):\n    if riders[i] >= riders[best]:\n        best = i\nprint(best + 1)"
        for mode, want in (("program", "내 코드만으로 돌렸더니 예시 1의 기대한 출력은 2인데 3이 나왔어요."), ("function", "내 코드만으로 돌렸더니 예시 `")):
            ctx = fakes.context(problem_text=fakes.PROGRAM_PROBLEM, plan=fakes.planned(blocks), open_count=2, guide=[fakes.service("빈칸?", 1)], mode=mode,
                                block_states={"b1": BlockState("b1", blocks[0].reference, "x", "Y")})
            done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code=code), {}, lambda *a, **k: failed)
            self.assertTrue(done["verdict"].seen.startswith(want), (mode, done["verdict"].seen))

    def test_guide_head_follows_the_starter(self):
        """시작 코드의 진입 함수 머리와 인자 이름·차례가 다른 가이드는 다시 만들고, 끝내 다르면 검증되지 않은 가이드다(실행하지 않는다)."""
        from ..llm import FakeLlm, use_llm
        from ..plan.nodes import solve

        starter = "fun solution(heights: IntArray, limit: Int): Int {\n    var answer = 0\n    return answer\n}"
        other = "fun solution(h: IntArray, k: Int): Int {\n    return h.count { it > k }\n}"
        solved = lambda code: {"clues": [], "approach": "센다.", "steps": ["센다"], "code": code}  # noqa: E731
        ctx = fakes.context(problem_text=fakes.KOTLIN_PROBLEM, language="kotlin", starter=starter)
        for scripts, want, runs in (([solved(other), solved(KOTLIN_CODE)], (KOTLIN_CODE, True), 1), ([solved(other)] * 3, (other, False), 0)):
            seen, fake = [], FakeLlm({"plan.solve": scripts})
            with use_llm(fake):
                got = solve({"ctx": ctx, "strategy": "fresh"}, {"configurable": {"check": lambda pid, code, quick=False: seen.append(code) or {"status": "passed"}}})
            self.assertEqual(((got["solution"].code, got["solution"].verified), len(seen)), (want, runs))
            self.assertIn(starter, fakes.prompt(fake, "plan.solve"))


    def test_given_guide_check_has_three_outcomes(self):
        """실린 정답 풀이를 이 기기에서 확인한 결과: 통과, 통과하지 못함, 채점하지 못함(도구·케이스가 없거나 채점기가 없음)."""
        from ..plan.nodes import _given_guide

        fixed = {"code": KOTLIN_CODE, "approach": "센다.", "steps": ["센다"], "clues": ["단서"]}
        ctx = fakes.context(problem_text=fakes.KOTLIN_PROBLEM, language="kotlin")
        graded = lambda status: (lambda pid, code, quick=False: {"status": status, "cases": []})  # noqa: E731
        for check, want in ((graded("passed"), True), (graded("failed"), False), (graded("timeout"), False), (graded("toolchain_missing"), None),
                            (graded("unsupported_signature"), None), (lambda pid, code, quick=False: None, None), (None, None)):  # 케이스 없음, 채점기 없음
            self.assertIs(_given_guide({"ctx": ctx}, fixed, check)["solution"].verified, want)


class OtherFeatureTest(unittest.TestCase):
    def test_followup(self):
        chair = [fakes.service("인용문장?", 0, "m1"), fakes.service("OTHER_CHAT_SECRET?", 0, "m2")]
        ctx = fakes.context(plan=fakes.planned(fakes.two() + [fakes.block(3, "뒤", "LATER_REF", "branch")]), open_count=1, chair=chair)
        done, fake = fakes.go(fakes.make_state("followup", ctx, mode="chair", quote_id="m1", text="왜 그래요"),
                              {"followup.answer": ["'제목이 같으면 같은 책입니다'(문제 글)라서요. 그럴 때 무엇을 놓칠까요?"]})
        body = fakes.prompt(fake, "followup.answer")
        self.assertIn("인용한 말:인용문장?", body)
        self.assertIn("(추론)", body)
        for leak in ("OTHER_CHAT_SECRET", "LATER_REF"):
            self.assertNotIn(leak, body)
        self.assertEqual(done["result"]["move"], "followup")
        self.assertNotIn("advance", done["result"])
        self.assertEqual(done["open_count"], 1)
        done, _ = fakes.go(fakes.make_state("followup", ctx, mode="chair", quote_id="m1", text="왜"), {"followup.answer": ["정답은 딕셔너리예요."]})
        self.assertEqual(done["result"]["reply"], FALLBACK["followup"])

    def test_syntax_example_passes(self):
        """문법을 물으면 대체 질문만 나왔다. 문제와 무관한 예의 코드 안 문자열은 인용 검사에서 뺀다."""
        ctx = fakes.context(plan=fakes.planned(fakes.two()), open_count=1, chair=[fakes.service("인용문장?", 0, "m1")])
        for answer in ("과일 이름으로 한 줄 보여 드리면, basket = deque(['사과', '배', '포도']) 같은 덱에서 basket.popleft()를 쓰면 맨 앞의 '사과'가 빠져요. "
                       "그러면 명단에서 맨 앞을 꺼낼 때는 무엇을 쓰면 될까요?",
                       "과일 이름으로 한 줄 보여 드리면, `basket = deque([\"사과\", \"배\", \"포도\"])` 같은 덱에서 `basket.popleft()`를 쓰면 맨 앞의 사과가 빠져요. "
                       "그러면 명단에서 맨 앞을 꺼낼 때는 무엇을 쓰면 될까요?"):
            done, _ = fakes.go(fakes.make_state("followup", ctx, mode="chair", quote_id="m1", text="덱에서 맨 앞을 꺼내는 법을 다른 예로 보여 줘요"),
                               {"followup.answer": [answer]})
            self.assertEqual(done["result"]["reply"], answer)

    def test_fill_returns_reference_without_model(self):
        ref = "    if load + w <= limit:\n        belt.append(w)"  # 들여쓰기의 차는 남는다(첫 줄 기준으로 놓는다)
        blocks = [fakes.block(1, "입력받기", "def solution(a):"), fakes.block(2, "올리기", ref, "condition")]
        done, fake = fakes.go(fakes.make_state("fill", fakes.context(plan=fakes.planned(blocks), open_count=2), block_id="b2"), {})
        self.assertEqual((done["result"]["code"], fake.calls, done["open_count"]), ("if load + w <= limit:\n    belt.append(w)", [], 2))  # 블록 칸은 알맹이를 맨 앞에 둔다

    def test_fill(self):
        """reference가 빈 옛 계획만 모델이 쓴다."""
        blocks = [replace(b, reference="") for b in fakes.two()] + [fakes.block(3, "뒤", "LATER_REF", "branch")]
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=2)
        done, fake = fakes.go(fakes.make_state("fill", ctx, block_id="b2", filled=[FilledBlock("b1", "a = 1")]),
                              {"fill.write_block": [{"code": "```python\nwhile True:\n    break\n```"}]})
        text = fakes.prompt(fake, "fill.write_block")
        self.assertIn("- 입력받기: a = 1", text)
        self.assertIn("변수 이름을 그대로", text)
        for leak in ("LATER_REF", "뒤 (branch)"):
            self.assertNotIn(leak, text)
        self.assertEqual(done["result"]["code"], "while True:\n    break")
        self.assertEqual(done["open_count"], 3)
        done, fake = fakes.go(fakes.make_state("fill", ctx, block_id="b2"), {"fill.write_block": [{"code": "x"}]})
        self.assertIn("- 입력받기: 비어 있음", fakes.prompt(fake, "fill.write_block"))

    def test_feedback(self):
        plan = replace(fakes.planned(fakes.two()), algorithm="binary_search")
        sub = Submission("s1", "print(1)", False)
        analysis = {"analysis": "같은 이름이 둘이면요? [확실] 제출은 실패다. 집합이 합친다.", "similar_hint": "범위를 반씩 줄인다", "advice": "정석 순서로"}
        done, fake = fakes.go(fakes.make_state("feedback", fakes.context(plan=plan, open_count=1, latest_submission=sub)),
                              {"feedback.assess": ["[check]49 Y"], "feedback.analyze": [analysis]})
        result = done["result"]
        self.assertEqual(result["strategy"], "canonical")
        self.assertEqual(result["similar_hint"], "이분탐색: 범위를 반씩 줄인다")
        self.assertTrue(result["analysis"].endswith("[추측] 집합이 합친다."))
        text = fakes.prompt(fake, "feedback.analyze")
        for must in ("[확실]", "[가능성 높음]", "[추측]", "제출 결과:실패", '"이분탐색: …"', "advice: 정석으로", "블록 방식을 쓰지 않고 혼자 풀었다"):
            self.assertIn(must, text)
        for solo in ("목표-NEXT_SECRET", "블록(정석 흐름 순서)", "정석 블록 순서", "'블록 n'"):  # 블록을 쓰지 않은 풀이에는 블록 이야기를 넘기지 않는다
            self.assertNotIn(solo, text)
        self.assertNotIn("REF_ONE", text)
        self.assertEqual(text.count("advice:"), 1)
        used = fakes.context(plan=plan, open_count=1, latest_submission=sub, chair=[fakes.service("q", 0, "m1")])  # 블록 방식으로 푼 사람에게는 블록 자료가 간다
        done, fake = fakes.go(fakes.make_state("feedback", used), {"feedback.assess": ["[check]49 Y"], "feedback.analyze": [analysis]})
        text = fakes.prompt(fake, "feedback.analyze")
        for must in ("목표-NEXT_SECRET", "블록(정석 흐름 순서)", "정석 블록 순서", "'블록 n'"):
            self.assertIn(must, text)
        empty = Submission("s2", "", True)
        done, fake = fakes.go(fakes.make_state("feedback", fakes.context(plan=plan, open_count=1, latest_submission=empty)), {"feedback.analyze": [analysis]})
        self.assertEqual((done["result"]["strategy"], fakes.tasks(fake)), ("fresh", ["feedback.analyze"]))
        fenced, _ = fakes.go(fakes.make_state("feedback", fakes.context(plan=plan, open_count=1, latest_submission=sub)),
                             {"feedback.assess": ["[check]50 Y"], "feedback.analyze": [{**analysis, "similar_hint": "```x```"}]})
        self.assertEqual(fenced["error"].code, "invalid_output")

    def test_feedback_gets_this_solve_record(self):
        sub = Submission("s1", "print(1)", True)
        chair = [fakes.service("q", 0, "m1"), fakes.user("몰라요", 0), fakes.service("q2", 0, "m2", "clue"), fakes.user("답 줘", 0, "u3"),
                 fakes.service(ANSWER_LEAD + "q4?", 0, "m4", "trace"), fakes.user("세요", 0, "u2"), fakes.service("q3", 1, "m3")]  # 답 조르기는 막힌 차례로 세지 않는다
        ctx = fakes.context(plan=fakes.planned(fakes.two()), open_count=2, latest_submission=sub, chair=chair,
                            block_states={"b2": BlockState("b2", "while x < 3:", "h", "Y", None, 2)},
                            debug_state=DebugState("h", "logic", 12, "< 대신 <=를 써야 한다.", "", 1, ""), failed_submissions=["wrong_answer", "wrong_answer"], hints_seen=1)
        done, fake = fakes.go(fakes.make_state("feedback", ctx), {"feedback.assess": ["[check]90 Y"], "feedback.analyze": [{"analysis": "a.", "similar_hint": "h", "advice": "c"}]})
        text = fakes.prompt(fake, "feedback.analyze")
        for must in ("이번 풀이의 기록", "블록 1(입력받기): 튜터의 질문으로 풀 때 이 블록에서 다음 블록으로 넘어가지 못한 답이 1번", "블록 2(NEXT_SECRET) 블록 코드 확인에서 튜터의 코드와 이어지지 않은 횟수 1번(틀렸다는 뜻이 아니다)",
                     "12번째 줄. < 대신 <=를 써야 한다.", "오답 2번", "본 힌트: 1개", "기록에 없으면 막힌 지점이 없었다고", "계산하지 않았으면 수를 말하지 않는다"):
            self.assertIn(must, text)

    def test_feedback_record_skips_misjudged_code_and_marks_counted_facts(self):
        """이름만 다른 맞는 코드를 모델이 틀렸다고 한 것이 '틀린 코드'로 세어졌고, 기록에서 센 사실에 [추측]이 붙었다."""
        sub = Submission("s1", "print(1)", True)
        chair = [fakes.service("q", 0, "m0"), fakes.user("모르겠어요", 0, "u0"), fakes.service("q?", 0, "m1", "clue"),
                 fakes.user("conveyor = deque()", 0, "u1"), fakes.service(RETRY_LEAD + "아직이에요.", 0, "m2", "done"),
                 fakes.user("belt = deque()", 0, "u2"), fakes.service("맞아요.", 0, "m3", "done"),
                 fakes.user("belt = deque()", 0, "u3"), fakes.service("맞아요.", 0, "m4", "done")]  # 통과한 코드를 다시 확인했다(tries는 그대로)
        ctx = fakes.context(plan=fakes.planned(fakes.two()), open_count=2, latest_submission=sub, chair=chair,
                            block_states={"b1": BlockState("b1", "belt = deque()", "h", "Y", None, 2)})
        analysis = {"analysis": "벨트에서 꺼낼 때 비어 있을 수 있을까요? 블록 1에서 다음 블록으로 넘어가지 못한 답이 1번이었습니다. 제출은 통과했습니다.",
                    "similar_hint": "h", "advice": "c"}
        done, fake = fakes.go(fakes.make_state("feedback", ctx), {"feedback.assess": ["[check]90 Y"], "feedback.analyze": [analysis]})
        self.assertNotIn("틀린 코드", fakes.prompt(fake, "feedback.analyze"))  # 튜터의 오판은 세지 않는다
        from ..feedback.prompts import record_lines
        wrongs = [fakes.user(f"x = {n}", 0, f"w{n}") for n in range(3)]
        tried = [m for w in wrongs for m in (w, fakes.service(RETRY_LEAD + "다시.", 0, "r" + w.id))] + chair[5:]
        lines = record_lines(fakes.context(chair=tried, block_states={"b1": BlockState("b1", "belt = deque()", "h", "Y", None, 4)}), fakes.planned(fakes.two()))
        self.assertIn("블록 1(입력받기) 블록 코드 확인에서 튜터의 코드와 이어지지 않은 횟수 3번", "\n".join(lines))  # 같은 맞는 코드를 두 번 확인해도 3번
        self.assertIn("[확실] 블록 1에서 다음 블록으로 넘어가지 못한 답이 1번이었습니다.", done["result"]["analysis"])
        from ..feedback.rules import mark_claims
        self.assertEqual(mark_claims("7번째 줄을 고쳤다.", "- 디버그: 틀린 곳은 7번째 줄."), "[확실] 7번째 줄을 고쳤다.")
        self.assertEqual(mark_claims("3번 틀렸다.", "- 본 힌트: 1개"), "[추측] 3번 틀렸다.")  # 기록에 없는 수

    def test_unchecked_block_answers_are_not_stuck(self):
        """블록 코드 확인의 글에는 판정이 남고, '확인 전'으로 끝난 확인은 막힌 답으로 세지 않는다(표시 없는 옛 기록은 그대로 읽는다)."""
        from ..common.talk_rules import CHECKED
        from ..feedback.prompts import PASSED_ADVICE, PASSED_RULE, analyze_messages, record_lines
        from ..save.nodes import collect
        from ..state import Verdict

        plan = fakes.planned(fakes.two())
        for verdict, unsure, mark in ((Verdict(False, unsure=True), True, "?"), (Verdict(True), False, "Y"), (Verdict(False), False, "N")):
            state = fakes.make_state("turn", fakes.context(plan=plan, open_count=2), mode="guide", event="block_filled", block_id="b1", code="x = 1")
            rows = collect({**state, "verdict": verdict, "result": {"reply": "말", **({"unsure": True} if unsure else {})}})["changes"]["messages"]
            self.assertEqual([row["move"] for row in rows if row["role"] == "user"], [CHECKED + mark])
        held = fakes.service("튜터의 뒤 코드는 값을 `data` 이름으로 이어 써요.", 0, "m1", "blank")
        marked = replace(fakes.user("x = 1", 0), move=CHECKED + "?")
        states = {"b1": BlockState("b1", "x = 1", "h", "Y", None, 1)}
        self.assertEqual(record_lines(fakes.context(guide=[marked, held], block_states=states), plan), [])
        old = record_lines(fakes.context(guide=[fakes.user("x = 1", 0), held], block_states=states), plan)
        self.assertTrue(any("넘어가지 못한 답이 1번" in line for line in old), old)  # 표시 없는 옛 기록은 전과 같게 읽는다
        talk = [fakes.user("모르겠는데 반복을 먼저 할까요", 0), fakes.service("무엇을 세야 할까요?", 0, "m2", "blank")]
        self.assertTrue(record_lines(fakes.context(guide=talk, block_states=states), plan))  # 말로 막힌 것은 그대로 센다
        for ok in (True, False):
            ctx = fakes.context(plan=plan, open_count=2, latest_submission=Submission("s1", "print(1)", ok), block_states=states)
            prompt = analyze_messages({**fakes.make_state("feedback", ctx), "strategy": "keep_flow"})[1]["content"]
            self.assertEqual((PASSED_RULE in prompt, PASSED_ADVICE in prompt, "고칠 곳" in prompt.split("advice:")[-1].split("\n")[0]), (ok, ok, not ok))

    def test_feedback_record_names_skipped_blocks(self):
        from ..feedback.prompts import record_lines
        from ..common.talk_rules import SKIPPED
        guide = [fakes.user("x = 1", 0, "u1"), fakes.service(SKIPPED + " 다음 블록이에요.", 0, "m1", "done")]
        lines = "\n".join(record_lines(fakes.context(guide=guide, block_states={"b1": BlockState("b1", "x = 1", "h", "?", None, 1)}), fakes.planned(fakes.two())))
        self.assertIn("블록 1(입력받기): '이대로 넘어가기'로 확인 없이 넘어감", lines)
        self.assertNotIn("넘어감", "\n".join(record_lines(fakes.context(guide=guide, block_states={"b1": BlockState("b1", "x = 1", "h", "Y", None, 1)}), fakes.planned(fakes.two()))))

    def test_llm_failure_clears_new_plan(self):
        done, _ = fakes.go(fakes.make_state("turn", fakes.context(), mode="guide", event="message", text="이름별로 세면 돼요"),
                           {**DRAFT, "guide.judge": [LlmFailed("공급자 오류")]})
        self.assertEqual(done["error"].code, "llm_failed")
        self.assertIsNone(done.get("plan"))


class InjectionTest(unittest.TestCase):
    def test_main_graph_calls_one_feature(self):
        called = []

        def agent(name):
            def node(state):
                called.append(name)
                if name == "context":
                    return {"ctx": fakes.context(), "open_count": 0}
                if name == "plan":
                    return {"plan": fakes.planned(fakes.two())}
                if name == "save":
                    return {"response": {"status": 200, "body": {}}}
                return {"result": {"reply": "답?", "advance": False}}

            return node

        compiled = build({name: agent(name) for name in AGENTS})
        done = compiled.invoke({"request": fakes.make_state("turn", fakes.context(), mode="guide", event="start")["request"]})
        self.assertEqual(called, ["context", "request_check", "plan", "guide", "output_check", "save"])
        self.assertEqual(done["response"]["status"], 200)


def own_check(seen: list, free: str = "REF_TWO"):
    """가짜 채점 함수: 튜터의 코드(free)가 이어진 프로그램은 틀리고, 그것 없이 내 블록만 이은 프로그램은 맞는다."""
    def check(problem_id, code, quick=False):
        seen.append(code)
        good = free not in code
        return {"status": "passed" if good else "failed", "compile": "",
                "cases": [{"id": "1", "kind": "accuracy", "status": "passed" if good else "failed", "input": "[]", "expected": "1", "got": "1" if good else "2", "error": ""}]}
    return check


class ThreeWayVerdictTest(unittest.TestCase):
    """통과 / 이어지지 않아요 / 확인 전: 이어 돌려 끝까지 돌았는데 통과하지 못하면 이어지지 않아요이고, 내 코드만으로 통과하면 통과이고, 넘어갈 길이 있다."""

    def turn(self, blocks, code, states=None, check=None, language="python", **extra):
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)], block_states=states or {}, language=language)
        return fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code=code, **extra), {}, check)

    def test_error_in_tutors_line_or_unknown_line_is_not_joined(self):
        # 내 블록이 order를 None으로 만들었다: 튜터의 뒤 블록의 줄에서 오류가 난다. 내 블록이 틀렸는지는 이 실행으로 알 수 없다
        done, _ = self.turn(SORT_BLOCKS, "order = None", check=sort_check([]))
        said = done["verdict"].seen
        self.assertEqual((done["block_check"].verdict, done["verdict"].unsure, done["verdict"].hint, done["block_check"].tries), ("N", False, False, 1))  # 튜터의 줄에서 났어도 이어지지 않아요다
        self.assertTrue(said.startswith("튜터의 코드(2번 블록 자리)에서 실행 오류가 났어요."), said)
        self.assertTrue(said.endswith(NOT_JOINED) and "`TypeError" in said and "틀렸" not in said, said)  # 사실 → 두 가지 가능성 → 할 수 있는 일
        self.assertEqual(done["result"]["reply"], RETRY_LEAD + said)
        self.assertNotIn("unsure", done["result"])
        # 채점기가 줄을 알려 주지 못한 오류도 마찬가지다
        no_line = lambda pid, code, quick=False: {"status": "runtime_error", "compile": "", "cases": [  # noqa: E731
            {"id": "1", "kind": "example", "status": "runtime_error", "input": "[[1]]", "expected": "1", "got": "", "error": "Traceback\nValueError: x"}]}
        done, _ = self.turn(SORT_BLOCKS, "order = sorted(items)", check=no_line)
        self.assertTrue(done["verdict"].seen.startswith("실행 오류가 났는데 어느 줄에서 났는지는 알 수 없어요."), done["verdict"].seen)
        self.assertEqual((done["block_check"].verdict, done["verdict"].unsure), ("N", False))

    def test_error_in_my_line_is_no(self):
        done, _ = self.turn(SORT_BLOCKS, "order = sorted(itemz)", check=sort_check([]))
        self.assertEqual((done["block_check"].verdict, done["verdict"].unsure, done["block_check"].tries - 0), ("N", False, 1))
        self.assertTrue(done["verdict"].seen.startswith("내 블록 1번째 줄(`order = sorted(itemz)`)에서 실행 오류가 났어요.\n`NameError: name 'itemz' is not defined`"), done["verdict"].seen)

    def test_wrong_value_without_tutor_code_is_plain_no(self):
        """튜터의 코드가 없는 프로그램(내 블록이 모두 있다)에서 값이 다르면 겹칠 수 있다는 말이 없다."""
        states = {"b1": passed_block("b1", "order = sorted(items)")}
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], block_states=states)
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="return order[0]"), {}, sort_check([]))
        self.assertEqual((done["block_check"].verdict, NOT_JOINED in done["verdict"].seen), ("N", False))
        self.assertEqual(done["verdict"].seen, "내 코드만으로 돌렸더니 예시 `solution([3, 1, 2])`의 기대한 값은 2인데 1이 나왔어요.")  # 튜터의 코드와 이은 것이 아니다: 한 일 그대로

    def test_infinite_loop_is_no_only_when_no_tutor_code_is_in_it(self):
        states = {"b1": passed_block("b1", "order = sorted(items)")}
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], block_states=states)
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="while True:\n    pass"), {},
                           exec_check([], SORT_CASES_ARGS, timeout_if="while"))
        self.assertEqual((done["block_check"].verdict, done["verdict"].unsure), ("N", False))  # 튜터의 코드 없이 끝나지 않는다: 내 블록이다

    def test_own_code_alone_passes(self):
        """튜터의 뒤 코드와 이어서는 틀려도, 지금까지의 내 블록만으로 모든 케이스를 통과하면 통과다(말하고, 확인 전이던 내 블록도 통과가 된다)."""
        seen = []
        states = {"b1": BlockState("b1", "x = 0", code_hash("x = 0"), "?")}
        blocks = [*fakes.hinted(), fakes.block(3, "뒤", "REF_TWO_LATER = 3", hints=list(fakes.HINTS1))]
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=2, guide=[fakes.service(fakes.HINTS2[0], 1)], block_states=states)
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="y = 1"), {}, own_check(seen, "REF_TWO_LATER"))
        self.assertEqual((fake.calls, done["block_check"].verdict, len(seen)), ([], "Y", 2))  # 이은 것, 내 블록만 이은 것
        self.assertEqual(seen[1], "x = 0\ny = 1")
        self.assertTrue(done["result"]["reply"].startswith(ALONE_OK), done["result"]["reply"])
        self.assertEqual([(f.block_id, f.verdict) for f in done["block_fixes"]], [("b1", "Y")])
        # 내 블록만으로도 통과하지 못하면 그 판정 그대로다
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b2", code="y = REF_TWO_LATER"), {}, own_check([], "REF_TWO_LATER"))
        self.assertNotEqual(done["block_check"].verdict, "Y")

    def test_skip_keeps_the_block_unchecked_and_opens_the_next(self):
        def never(*args, **kwargs):
            raise AssertionError("넘어가기는 실행하지 않는다")

        saved = BlockState("b1", "order = sorted(itemz)", code_hash("order = sorted(itemz)"), "N", tries=2)
        done, fake = self.turn(SORT_BLOCKS, "order = sorted(itemz)", {"b1": saved}, never, quiet=True, skip=True)
        self.assertEqual((fake.calls, done["block_check"].verdict, done["block_check"].tries - 1, done["open_count"]), ([], "?", 2, 2))  # 틀린 수(tries − 1)는 그대로 2다
        self.assertTrue(done["result"]["reply"].startswith(SKIPPED), done["result"]["reply"])
        self.assertTrue(done["result"]["unsure"] and done["result"]["advance"])
        self.assertEqual(done["block_check"].code, "order = sorted(itemz)")  # 칸의 글은 그대로 남는다

    def test_malformed_model_verdict_is_unchecked(self):
        """채점 함수가 없어 모델이 읽는데 답이 형식에 맞지 않았다: 틀린 코드가 아니라 확인 전이다."""
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)])
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="order = sorted(items)"),
                              {"guide.check_code": ["판단하기 어렵습니다"]})
        self.assertEqual((done["block_check"].verdict, done["verdict"].seen, done["block_check"].tries, done["open_count"]), ("N", MALFORMED, 0, 1))
        self.assertEqual(done["result"]["reply"], MALFORMED)

    def test_examples_only_is_said_once_per_problem(self):
        example = lambda pid, code, quick=False: {"status": "passed", "cases": [{"kind": "example", "status": "passed"}]}  # noqa: E731
        done, _ = self.turn(SORT_BLOCKS, "order = sorted(items)  # ", check=example)
        self.assertTrue(done["verdict"].seen == EXAMPLES_ONLY and done["result"]["reply"].startswith(EXAMPLES_ONLY), done["verdict"].seen)
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(EXAMPLES_ONLY + " 다음?", 0)])
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="order = sorted(items)  # "), {}, example)
        self.assertEqual((done["block_check"].verdict, done["verdict"].seen), ("Y", ""))  # 이미 말했다: 다시 말하지 않는다

    def test_multi_line_output_is_a_box(self):
        from ..turn.code_check import seen_line

        case = {"id": "1", "kind": "example", "input": "5\n", "expected": "3\n0\n2\n", "got": "3\n1\n2\n", "status": "failed"}
        said = seen_line({"status": "failed", "cases": [case]}, True, "뒤 블록을 튜터의 코드로 이어 돌리면")
        self.assertEqual(said, "뒤 블록을 튜터의 코드로 이어 돌리면 예시 1의 출력이 기대와 달라요.\n기대한 출력:\n```\n3\n0\n2\n```\n내 출력:\n```\n3\n1\n2\n```")
        self.assertEqual(seen_line({"status": "failed", "cases": [{**case, "expected": "3\n", "got": "2\n"}]}, True), "예시 1의 기대한 출력은 3인데 2가 나왔어요.")  # 한 줄은 문장 안에


    def test_multi_line_output_passes_the_fence_guard(self):
        """엔진이 넣은 글상자는 말풍선의 코드 펜스 검사에 걸리지 않는다(모델이 쓴 펜스는 여전히 거른다)."""
        failed = lambda pid, code, quick=False: {"status": "failed", "compile": "", "cases": [  # noqa: E731
            {"id": "1", "kind": "example", "status": "failed", "input": "5\n", "expected": "3\n0\n", "got": "3\n1\n", "error": ""}]}
        ctx = fakes.context(plan=fakes.planned(SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)], mode="program")
        done, _ = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="order = 1"), {}, failed)
        self.assertIsNone(done.get("error"))
        self.assertIn("기대한 출력:\n```\n3\n0\n```", done["result"]["reply"])
        self.assertNotIn("boxed", done["result"])


class StarterFrameTest(unittest.TestCase):
    """시작 코드의 가져오기 줄을 지키고, 튜터의 풀이를 믿을 수 없을 때는 시작 코드의 틀 안에 내 블록을 놓는다."""

    def test_starter_imports_are_kept(self):
        from ..common.solution import composed_parts, spliced, spliced_view

        refs = ["import java.util.ArrayDeque;\n\nclass Solution {\n    public int solution(int[] a) {\n        int total = 0;", "        return total;\n    }\n}"]
        starter = "import java.util.*;\n\nclass Solution {\n    public int solution(int[] a) {\n        return 0;\n    }\n}"
        text, spans = spliced_view(refs, 0, "int total = new ArrayList<Integer>().size();", "java", {}, None, False, starter)
        self.assertTrue(text.startswith("import java.util.ArrayDeque;\nimport java.util.*;\n"), text)  # 튜터 풀이의 것과 합친다(가져오기 줄들 뒤에)
        first = next(s for s in spans if s["whose"] == "this")
        self.assertEqual(text.splitlines()[first["first"] - 1].strip(), "int total = new ArrayList<Integer>().size();")  # 줄 번호는 더한 줄만큼 밀린다
        self.assertEqual(spliced(refs, 0, "int total = 0;", "java", {}, None, False, starter).count("import java.util.*;"), 1)
        for language in ("go", "rust", "javascript"):  # 쓰지 않은 가져오기·같은 이름의 두 번 선언이 오류가 되는 언어는 더하지 않는다
            self.assertNotIn("fmt", spliced(["func solution() int {\n    x := 1", "    return x\n}"], 0, "x := 1", language, {}, None, False, 'import "fmt"'))
        blocks = [fakes.block(1, "준비", refs[0]), fakes.block(2, "끝", refs[1])]
        parts = composed_parts(blocks, {"b1": {"code": "int total = 0;"}, "b2": {"code": "return total;"}}, "java", starter=starter)
        self.assertTrue(parts[0][1].startswith("import java.util.ArrayDeque;\nimport java.util.*;"), parts[0][1])

    def test_unverified_guide_composes_into_the_starter_frame(self):
        from ..common.solution import composed_parts

        blocks = [fakes.block(1, "준비", "rows = len(board)\ncols = len(board[0])"), fakes.block(2, "끝", "pass  # 여기서 칸을 본다")]  # 믿을 수 없는 계획 코드(틀이 없다)
        starter = "def solution(a):\n    answer = 0\n    return answer\n"
        codes = {"b1": {"code": "h, w = len(a), len(a[0])"}, "b2": {"code": "return h * w"}}
        parts = composed_parts(blocks, codes, "python", starter=starter, trusted=False)
        text = "\n".join(row for _, part in parts for row in part.split("\n") if "# 블록" not in row)
        self.assertEqual(text, "def solution(a):\n    h, w = len(a), len(a[0])\n    return h * w")
        trusted = composed_parts(blocks, codes, "python", starter=starter)  # 믿을 수 있으면 지금처럼 계획 코드의 틀
        self.assertNotIn("def solution", "\n".join(part for _, part in trusted))

    def test_fill_tidies_notes_and_indent_of_the_block_cell(self):
        from ..fill.nodes import tidy

        self.assertEqual(tidy("        # 설명 주석\n        count += 1  # 하나 센다\n\n        total = 0", "python", 8), "count += 1\n\ntotal = 0")
        self.assertEqual(tidy("        // 설명\n        x += 1;  // 늘린다\n        s = \"a // b\";", "java", 8), "x += 1;\ns = \"a // b\";")  # 문자열 안의 //는 주석이 아니다
        self.assertEqual(tidy("    for x in a:\n        n += x\n  return n", "python", 0), "    for x in a:\n        n += x\n  return n")  # 바깥으로 나가는 줄이 있으면 들여쓰기의 차를 지킨다


class ShownKindTest(unittest.TestCase):
    def test_label_only_when_the_code_makes_a_name(self):
        from ..common.solution import shown_kind

        make = lambda ref, kind="var_during": fakes.block(1, "x", ref, kind)  # noqa: E731
        self.assertEqual(shown_kind(make("answer = []"), "python"), "var_during")
        self.assertEqual(shown_kind(make("    return answer"), "python"), "")  # 값을 돌려주는 블록은 '풀이 중에 만드는 변수'가 아니다
        self.assertEqual(shown_kind(make("System.out.println(sb);\n    }\n}"), "java"), "")
        self.assertEqual(shown_kind(make("    for x in xs:\n        n += x", "loop"), "python"), "loop")  # 다른 종류는 모델이 붙인 것을 둔다
        self.assertEqual(shown_kind(make("", "var_during"), "python"), "var_during")  # 참고 코드가 빈 옛 계획은 그대로


class ErrorRowLineTest(unittest.TestCase):
    def test_program_line_numbers_are_not_shown(self):
        from ..turn.code_check import _error_row

        self.assertEqual(_error_row("IndentationError: expected an indented block after 'if' statement on line 13"), "IndentationError: expected an indented block after 'if' statement")
        self.assertEqual(_error_row("SyntaxError: '(' was never closed", whole=True), "SyntaxError: '(' was never closed")
        self.assertEqual(_error_row("ValueError: missed deadline 5 (line 7)", whole=True), "ValueError: missed deadline 5")  # 낱말 안의 'line'은 줄 번호가 아니다


def stdin_check(seen: list, cases: list):
    """가짜 채점 함수(표준 입출력): 받은 프로그램을 케이스마다 표준 입력으로 돌린다. cases: [(입력, 기대 출력, kind)]."""
    import contextlib
    import io

    def check(problem_id, code, quick=False):
        seen.append(code)
        rows = []
        for n, (given, want, kind) in enumerate(cases, 1):
            out, case = io.StringIO(), {"id": str(n), "kind": kind, "input": given, "expected": want, "got": "", "error": ""}
            feed = iter(given.splitlines())

            def read(prompt=""):
                try:
                    return next(feed)
                except StopIteration:
                    raise EOFError("EOF when reading a line") from None
            try:
                with contextlib.redirect_stdout(out):
                    exec(code, {"input": read})
                case["got"] = out.getvalue()
                case["status"] = "passed" if out.getvalue().strip() == want.strip() else "failed"
            except Exception as exc:  # noqa: BLE001
                case.update(status="runtime_error", error=f"Traceback (most recent call last):\n{type(exc).__name__}: {exc}", line=line_of(exc))
            rows.append(case)
        return {"status": next((c["status"] for c in rows if c["status"] != "passed"), "passed"), "cases": rows, "compile": ""}
    return check


TWICE = [fakes.block(1, "읽기", "n = int(input())", hints=list(fakes.HINTS1)), fakes.block(2, "두 배", "m = n * 2", "var_during", hints=list(fakes.HINTS2)),
         fakes.block(3, "출력", "print(m)", hints=list(fakes.HINTS1))]
TWICE_CASES = [("3", "6", "example"), ("5", "10", "accuracy")]


class MyBlocksAloneTest(unittest.TestCase):
    """내 블록만으로 돌리기는 내가 쓴 블록을 모두 잇고(모아서 실행과 같은 글), 숨은 테스트가 있을 때만 통과시킨다. 확인 전 블록이 낀 실패는 확인 전이다."""

    def turn(self, states, block_id, code, cases=TWICE_CASES, open_count=2, **extra):
        seen = []
        ctx = fakes.context(plan=fakes.planned(TWICE), open_count=open_count, guide=[fakes.service("빈칸?", open_count - 1)], block_states=states, mode="program", **extra)
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id=block_id, code=code), {}, stdin_check(seen, cases))
        return done, seen

    def test_block_that_did_not_pass_is_in_the_run(self):
        states = {"b1": BlockState("b1", "x = input()", code_hash("x = input()"), "N", tries=2)}
        done, seen = self.turn(states, "b2", "n = int(input())\nprint(n * 2)")
        self.assertNotEqual(done["block_check"].verdict, "Y", done["verdict"].seen)
        self.assertFalse(done["result"]["reply"].startswith(ALONE_OK))
        self.assertTrue(any(code.startswith("x = input()\nn = int(input())") for code in seen), seen)  # 화면에 적힌 내 글을 모두 이었다

    def test_examples_only_does_not_pass_my_blocks_alone(self):
        done, _ = self.turn({}, "b1", "print(6)", cases=[("3", "6", "example")], open_count=1)
        self.assertNotEqual(done["block_check"].verdict, "Y", done["verdict"].seen)
        states = {"b1": BlockState("b1", "n = int(input())", code_hash("n = int(input())"), "?"), "b3": passed_block("b3", "print(m)")}
        done, _ = self.turn(states, "b2", "m = n * 2", cases=[("3", "6", "example")])  # 튜터의 코드 없이 통과했지만 공개 예시뿐: 확인 전 블록을 올리지 않는다
        self.assertEqual(done["block_check"].verdict, "Y")
        self.assertEqual(done["block_fixes"], [])

    def test_failure_with_an_unchecked_block_is_unchecked(self):
        from ..common.talk_rules import UNCHECKED_IN

        states = {"b1": BlockState("b1", "n = int(input()) + 1", code_hash("n = int(input()) + 1"), "?", tries=0)}
        done, _ = self.turn(states, "b2", "m = 2 * n")
        self.assertTrue(done["verdict"].unsure, done["verdict"].seen)
        self.assertIn(UNCHECKED_IN.format(blocks="1"), done["verdict"].seen)
        self.assertEqual((done["block_check"].tries, done["verdict"].hint), (0, False))  # 틀린 수·힌트를 붙이지 않는다
        self.assertNotIn(fakes.HINTS2[1], done["result"]["reply"])

    def test_many_answers_is_unchecked(self):
        from ..common.talk_rules import MANY_ANSWERS

        states = {"b1": passed_block("b1", "n = int(input())")}
        done, _ = self.turn(states, "b2", "m = n * 3", many_answers=True)
        self.assertEqual((done["verdict"].seen, done["verdict"].unsure, done["block_check"].tries), (MANY_ANSWERS, True, 0))
        done, _ = self.turn(states, "b2", "m = n * 3")  # 표시가 없으면 값이 다른 것은 그대로 말한다
        self.assertFalse(done["verdict"].unsure)

    def test_cut_without_named_pairs_is_unchecked(self):
        from ..turn.code_check import GUESSED_CUT, assumed, failure_verdict

        self.assertEqual(assumed([["x", "x"]], True), GUESSED_CUT.strip())  # 같은 이름끼리라 짝 말이 비어도 다 시도하지 못한 사실은 말한다
        report = {"status": "failed", "cases": [{"kind": "example", "status": "failed", "input": "3", "expected": "6", "got": "7"}]}
        got = failure_verdict(report, [], True, "", False, assumed([], True), True)
        self.assertTrue(got.unsure and GUESSED_CUT.strip() in got.seen and NOT_JOINED not in got.seen, got.seen)


class UnverifiedComposeTest(unittest.TestCase):
    def test_my_head_and_tail_lines_are_not_doubled(self):
        from ..common.solution import composed_parts

        blocks = [fakes.block(1, "준비", "m = n"), fakes.block(2, "끝", "return m * 2")]
        codes = {"b1": {"code": "def solution(n):\n    m = n"}, "b2": {"code": "return m * 2"}}
        text = "\n".join(row for _, part in composed_parts(blocks, codes, "python", starter="def solution(n):\n    answer = 0\n    return answer", trusted=False)
                         for row in part.split("\n") if "블록" not in row)
        self.assertEqual(text, "def solution(n):\n    m = n\n    return m * 2")
        starter = "import java.util.*;\n\nclass Solution {\n    public int solution(int n) {\n        int answer = 0;\n        return answer;\n    }\n}"
        codes = {"b1": {"code": "class Solution {\n    public int solution(int n) {\n        int m = n;\n        for (int i = 0; i < 2; i++) {"},
                 "b2": {"code": "            m += 0;\n        }\n        return m * 2;\n    }\n}"}}
        text = "\n".join(part for _, part in composed_parts(blocks, codes, "java", starter=starter, trusted=False))
        self.assertEqual((text.count("class Solution"), text.count("{"), text.count("}")), (1, 3, 3), text)  # 반복을 닫는 '}'는 남기고 틀의 괄호는 한 벌
        self.assertTrue(text.startswith("import java.util.*;"), text)


class ImportPlaceTest(unittest.TestCase):
    def test_added_imports_go_after_the_imports(self):
        from ..common.solution import spliced_view

        refs = ["#include <vector>\nint solution(std::vector<int> a) {\n    int s = a.size();", "    return s;\n}"]
        text, spans = spliced_view(refs, 0, "int s = a.size();", "cpp", {}, None, False, "#include <vector>\nusing namespace std;")
        self.assertTrue(text.startswith("#include <vector>\nusing namespace std;\n"), text)
        this = next(s for s in spans if s["whose"] == "this")
        self.assertEqual(text.splitlines()[this["first"] - 1].strip(), "int s = a.size();")  # 줄 번호는 넣은 줄 뒤만 밀린다
        refs = ["from __future__ import annotations\ndef solution(a):\n    s = len(a)", "    return s"]
        text, _ = spliced_view(refs, 0, "s = len(a)", "python", {}, None, False, "import math\ndef solution(a):\n    return 0")
        self.assertTrue(text.startswith("from __future__ import annotations\nimport math\n"), text)


class OwnWayTest(unittest.TestCase):
    """'끝까지 내 방식으로 쓰기': 지금 블록은 넘어가기와 같게 확인 전으로 두고 남은 블록을 모두 연다. 실행·모델 0회, 통과(Y)를 새로 만들지 않는다."""

    def test_opens_every_block_without_a_new_pass(self):
        from ..common.talk_rules import OWN_WAY

        def never(*args, **kwargs):
            raise AssertionError("내 방식으로 쓰기는 실행하지 않는다")

        def turn(**extra):
            ctx = fakes.context(plan=fakes.planned(TWICE), open_count=1, guide=[fakes.service("빈칸?", 0)], mode="program")
            return fakes.go(fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="x = input()", quiet=True, skip=True, **extra), {}, never)

        done, fake = turn(own_way=True)
        self.assertEqual((fake.calls, done["open_count"], done["block_check"].verdict), ([], len(TWICE), "?"))  # 열린 블록 수가 끝이다(셋)
        self.assertEqual([f for f in done.get("block_fixes") or [] if f.verdict == "Y"], [])  # 통과가 새로 생기지 않는다
        self.assertEqual((done["result"]["reply"], done["result"]["advance"]), (SKIPPED + " " + OWN_WAY, True))
        done, _ = turn()  # 표시 없이 넘어가면 지금처럼 한 블록만 더 연다
        self.assertEqual(done["open_count"], 2)
