"""튜터 말의 꼴: 두 칸 출력({"note", "question"}), 결정적 검사, 뜻이 안 바뀌는 후처리, 줄 조립, 긴 글의 꼴. 가짜 모델만 쓴다."""

import json
import re
import unittest
from pathlib import Path

from . import fakes
from . import test_pipeline as tp
from ..common.talk_prompts import NOT_SAID
from ..common.talk_rules import ANSWER_LEAD, FALLBACK, FILL_TIP, RETRY_LEAD, drop_echo
from ..turn.context import prepare

DASH = "—"
OLD_PLAN = fakes.planned(fakes.two())  # 저장 힌트가 없는 계획이라 모델이 말한다
ASK = ["chair.judge", "chair.ask"]
USER = "제목이 같은 책을 같은 묶음으로 봤어요"
NOTE = "제목이 같은 책을 한 묶음으로 보셨어요."
QUESTION = "`groups[3]`의 값은 얼마인가요?"


def talk(question, note="", text=USER, problem=None, judge="[check]N"):
    """모델이 말하는 한 번의 차례. (결과, 가짜 모델). 모델 출력은 두 칸이다."""
    extra = {"problem_text": problem} if problem else {}
    state = tp.chair_state(text, chair=[fakes.service(fakes.HINTS1[0], 0)], plan=OLD_PLAN, **extra)
    return fakes.go(state, {"chair.judge": [judge], "chair.ask": [{"note": note, "question": question}]})


def lines(reply):
    return [part.strip() for part in reply.split("\n") if part.strip()]


class TwoFieldTest(unittest.TestCase):
    def test_lines_are_question_then_note(self):
        done, fake = talk(QUESTION, NOTE)
        self.assertEqual(fakes.tasks(fake), ASK)
        self.assertEqual(lines(done["result"]["reply"]), [QUESTION, NOTE])
        self.assertIn("\n", done["result"]["reply"])  # 줄바꿈으로 나눈다
        done, _ = talk(QUESTION, "")
        self.assertEqual(done["result"]["reply"].strip(), QUESTION)  # note가 없으면 질문 하나

    def test_code_form_question_passes(self):
        done, _ = talk("`groups[3]`의 값은 얼마인가요?")
        self.assertEqual(done["result"]["reply"].strip(), "`groups[3]`의 값은 얼마인가요?")

    def test_prompt_asks_for_the_two_fields(self):
        _, fake = talk(QUESTION)
        sent = fakes.prompt(fake, "chair.ask")
        self.assertIn("note", sent)
        self.assertIn("question", sent)
        self.assertIn("JSON", sent)


class BrokenJamoTest(unittest.TestCase):
    def test_the_users_example_goes_to_the_fallback(self):
        done, fake = talk("parent 배열에서 3번 칸의 ㄱ밧은 얼마인가요?", NOTE)
        reply = done["result"]["reply"]
        self.assertEqual(fakes.tasks(fake), ASK)  # 다시 부르지 않는다
        self.assertNotIn("ㄱ밧", reply)
        self.assertIn(FALLBACK[done["result"]["move"]], lines(reply))

    def test_vowel_jamo_is_caught_too(self):
        done, fake = talk("그 칸의 값ㅏ은 얼마인가요?")
        self.assertEqual(fakes.tasks(fake), ASK)
        self.assertEqual(done["result"]["reply"].strip(), FALLBACK[done["result"]["move"]])

    def test_jamo_in_the_problem_or_the_users_words_passes(self):
        asked = "ㅋㅋ 표시는 몇 번 나오나요?"
        done, _ = talk(asked, problem=fakes.PROBLEM + "\n(ㅋㅋ는 웃음 표시입니다.)")
        self.assertEqual(done["result"]["reply"].strip(), asked)
        asked = "말씀한 ㅎㅎ는 몇 번 나오나요?"
        done, _ = talk(asked, text="ㅎㅎ 같은 건 같은 묶음으로 봤어요")
        self.assertEqual(done["result"]["reply"].strip(), asked)

    def test_jamo_only_in_the_note_drops_just_the_note(self):
        done, fake = talk(QUESTION, "그 칸의 ㄱ밧을 보셨어요.")
        self.assertEqual(fakes.tasks(fake), ASK)
        self.assertEqual(done["result"]["reply"].strip(), QUESTION)


class LimitsTest(unittest.TestCase):
    def fallback(self, question, note=""):
        done, fake = talk(question, note)
        self.assertEqual(fakes.tasks(fake), ASK, question)  # 다시 부르지 않는다
        self.assertEqual(done["result"]["reply"].strip(), FALLBACK[done["result"]["move"]], question)

    def test_question_is_one_ask_in_one_sentence(self):
        self.fallback("이름을 세면 어떻게 되나요? 그 값은 얼마인가요?")
        self.fallback("이름을 세어 둔다고 하셨어요. 그 값은 얼마인가요?")

    def test_question_length_limit_is_120(self):
        def sized(n):
            return "책" * (n - 10) + " 값은 무엇인가요?"

        done, _ = talk(sized(120))
        self.assertEqual(done["result"]["reply"].strip(), sized(120))
        self.fallback(sized(121))

    def test_note_limits_drop_only_the_note(self):
        def sized(n):
            return "책" * (n - 1) + "."

        done, _ = talk(QUESTION, sized(80))
        self.assertEqual(lines(done["result"]["reply"]), [QUESTION, sized(80)])
        for note in (sized(81), "제목이 같다고 보셨어요. 묶음이 하나라고도 보셨어요."):
            done, fake = talk(QUESTION, note)
            self.assertEqual(fakes.tasks(fake), ASK)
            self.assertEqual(done["result"]["reply"].strip(), QUESTION, note)

    def test_existing_checks_still_hold(self):
        self.fallback("맞아요, 그 칸의 값은 얼마인가요?")  # 동의로 시작
        self.fallback("그 정답을 `groups[3]`에서 찾으면 값은 얼마인가요?")  # 금지 표현
        self.fallback("REF_ONE 줄이 하는 일은 무엇인가요?")  # 참고 코드
        self.fallback("NEXT_SECRET을 먼저 정하면 값은 얼마인가요?")  # 뒤 블록 이름


class FixesTest(unittest.TestCase):
    """뜻이 안 바뀌는 후처리. 걸러내지 않고 고친다."""

    def fixed(self, question):
        done, fake = talk(question)
        self.assertEqual(fakes.tasks(fake), ASK)
        return done["result"]["reply"].strip()

    def test_dash_becomes_comma(self):
        reply = self.fixed(f"제목이 같으면 {DASH} 몇 번 나왔는지 어디에 적나요?")
        self.assertNotIn(DASH, reply)
        self.assertIn(",", reply)
        self.assertIn("몇 번 나왔는지 어디에 적나요?", reply)

    def test_wording_fixes(self):
        self.assertIn("저장되나요?", self.fixed("그 값은 어디에 저장되어지나요?"))
        self.assertNotIn("되어지", self.fixed("그 값은 어디에 저장되어지나요?"))
        reply = self.fixed("사서가 책을 꽂은 뒤에 무엇을 하였나요?")
        self.assertIn("했나요?", reply)
        self.assertNotIn("하였", reply)
        reply = self.fixed("그  값은   어디에 저장하나요??")
        self.assertNotIn("  ", reply)
        self.assertEqual(reply[-2:], "요?")

    def test_code_and_problem_quotes_are_left_alone(self):
        span = f"`a  {DASH}  b`"
        self.assertIn(span, self.fixed(f"{span}의 값은 얼마인가요?"))
        quoted = "'사서는 어제 책을 정리하였습니다'에서 정리한 책은 어떤 책인가요?"
        done, _ = talk(quoted, problem=fakes.PROBLEM + "\n사서는 어제 책을 정리하였습니다.")
        self.assertEqual(done["result"]["reply"].strip(), quoted)


class EchoCheckTest(unittest.TestCase):
    def test_prompt_no_longer_recommends_you_saw_phrase(self):
        self.assertNotIn("보셨네요", NOT_SAID)

    def test_you_saw_ending_is_dropped_as_an_echo(self):
        got = drop_echo("2번과 3번을 같은 묶음으로 보셨네요. `groups[3]`의 값은 얼마인가요?")
        self.assertEqual(got, "`groups[3]`의 값은 얼마인가요?")


class AssemblyTest(unittest.TestCase):
    def test_result_line_comes_before_the_question(self):
        ctx = fakes.context(plan=fakes.planned(tp.SORT_BLOCKS), open_count=1, guide=[fakes.service(fakes.HINTS1[0], 0)])
        state = fakes.make_state("turn", ctx, mode="guide", event="block_filled", block_id="b1", code="arr = list(items)")
        done, fake = fakes.go(state, {}, tp.sort_check([]))
        seen = done["verdict"].seen
        self.assertEqual(fake.calls, [])
        self.assertEqual(re.sub(r"\n+", "\n", done["result"]["reply"]), RETRY_LEAD + seen + "\n" + fakes.HINTS1[1])

    def test_route_guides_come_after_the_question_on_their_own_line(self):
        chair = [fakes.service(fakes.HINTS1[0], 0)]
        done, fake = fakes.go(tp.chair_state("그냥 답 코드 알려 줘", chair=chair), {})
        self.assertEqual(fake.calls, [])
        self.assertEqual(lines(done["result"]["reply"]), [fakes.HINTS1[1], ANSWER_LEAD.strip()])

    def test_hint_count_and_fill_tip_survive_the_new_lines(self):
        talked = [fakes.service(fakes.HINTS1[0], 0, "m1"), fakes.user("모르겠어요", 0, "u1"), fakes.service("명단에서 무엇을 셀까요?", 0, "m2", "clue")]
        done, fake = fakes.go(tp.chair_state("잘 모르겠음", chair=talked), {})
        reply = done["result"]["reply"]
        self.assertEqual(fake.calls, [])
        self.assertEqual(lines(reply), [fakes.HINTS1[1], FILL_TIP.strip()])
        again = tp.chair_state("모르겠어요", chair=[*talked, fakes.user("잘 모르겠음", 0, "u2"), fakes.service(reply, 0, "m3", done["result"]["move"])])
        turn = prepare(again)["turn"]
        self.assertTrue(turn.tipped)
        self.assertEqual(turn.hints_seen, 2)  # 처음 힌트와 지금 낸 힌트


STRUCTURE = ("첫 줄", "결론", "목록", "다음 할 일")


class LongTextShapeTest(unittest.TestCase):
    def has_structure(self, text):
        for word in STRUCTURE:
            self.assertIn(word, text, word)

    def test_explain_and_feedback_prompts_ask_for_the_shape(self):
        state = fakes.make_state("explain", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1))
        _, fake = fakes.go(state, {"explain.write": [{"sections": fakes.SECTIONS}]})
        self.has_structure(fakes.prompt(fake, "explain.write"))
        plan = fakes.planned(fakes.two())
        analysis = {"analysis": "분석이다.", "similar_hint": "힌트", "advice": "조언"}
        state = fakes.make_state("feedback", fakes.context(plan=plan, open_count=1, latest_submission=tp.Submission("s1", "print(1)", False)))
        _, fake = fakes.go(state, {"feedback.assess": ["[check]49 Y"], "feedback.analyze": [analysis]})
        self.has_structure(fakes.prompt(fake, "feedback.analyze"))

    def test_debug_prompt_asks_for_the_shape(self):
        from ..debug.prompts import speak_messages

        state = fakes.make_state("debug", fakes.context(), text="왜")
        state["draft"] = {"line": 4, "cause": "원인", "fixed_line": "x", "recent": [], "step_name": "fix"}
        self.has_structure("\n".join(m["content"] for m in speak_messages(state)))

    def test_a_long_explain_is_recorded_not_redone(self):
        long_first = "이 풀이는 이름을 세는 방법이고 그래서 먼저 이름을 모두 읽은 뒤에 같은 이름을 묶어서 센다. 그리고 한 번 더 읽는다.\n" + "\n".join(f"- 항목 {n}" + "책" * 100 for n in range(7))
        sections = [{"title": row["title"], "body": long_first} for row in fakes.SECTIONS]
        state = fakes.make_state("explain", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1))
        done, fake = fakes.go(state, {"explain.write": [{"sections": sections}]})
        self.assertEqual(fakes.tasks(fake), ["explain.write"])  # 어겨도 다시 부르지 않는다
        self.assertIsNone(done.get("error"))
        self.assertEqual(done["result"]["explain"].sections[0].body, long_first)  # 글은 그대로 남는다


class BuiltinDataTest(unittest.TestCase):
    PROBLEMS = Path(__file__).resolve().parents[2] / "ui" / "problems"

    def test_plan_prompt_uses_parentheses_for_the_why(self):
        source = (Path(__file__).resolve().parents[1] / "plan" / "prompts.py").read_text(encoding="utf-8")
        self.assertIn("무엇을 한다(왜)", source)
        self.assertNotIn(f"무엇을 한다 {DASH} 왜", source)

    def test_builtin_ready_text_has_no_dash(self):
        found = []

        def walk(node, where):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key not in ("code", "reference"):
                        walk(value, f"{where}.{key}")
            elif isinstance(node, list):
                for n, value in enumerate(node):
                    walk(value, f"{where}[{n}]")
            elif isinstance(node, str) and DASH in re.sub(r"```.*?```|`[^`\n]*`", "", node, flags=re.S):
                found.append(f"{where}: {node[:40]}")

        files = sorted(self.PROBLEMS.glob("*/*/ready.json"))
        self.assertGreater(len(files), 50)
        for path in files:
            walk(json.loads(path.read_text(encoding="utf-8")), path.parent.name)
        self.assertFalse(found, f"줄표가 남은 글 {len(found)}곳, 처음 셋: {found[:3]}")


if __name__ == "__main__":
    unittest.main()
