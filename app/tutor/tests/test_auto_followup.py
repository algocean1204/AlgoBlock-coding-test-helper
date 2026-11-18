"""말 가르기(그래프 전체, 가짜 모델). 되묻는 말인지 블록의 답인지는 지금의 판정 호출 한 번이 가른다(판정 [check]Q).
되묻는 말에는 설명한 뒤 원래 질문으로 돌아오고, 진행(열린 블록 수, 힌트 번호)은 그대로다. 추가 호출은 없다.
내용 없는 말과 답 요청은 규칙이 가른다(모델 0회). 실제 모델로 재는 오분류는 ALGOBLOCK_LIVE=1일 때만 돈다."""

import os
import unittest
from dataclasses import replace

from . import fakes
from . import talk_bank as bank
from .test_advance_rule import ASK, ASKED, BLOCKS, CASES, HINTS, N, OPENING, PASS, checked, context, is_write, said, saved
from .test_pipeline import exec_check
from ..chair.prompts import MOVE_TEXT as CHAIR_STEPS
from ..common.verdict import parse_verdict
from ..guide.prompts import MOVE_TEXT as GUIDE_STEPS
from ..main import run
from ..save.respond import shown_count
from ..state import Block
from ..turn.moves import asks, rule_verdict

STEPS = {"chair": CHAIR_STEPS, "guide": GUIDE_STEPS}
GRAMMAR = "파이썬에서 for 문은 어떻게 써요?"
EXPLAIN = ("for는 모음에서 값을 하나씩 꺼내 같은 일을 되풀이하는 문법이에요. 예를 들어 `for fruit in fruits:` 아래에 `print(fruit)`를 두면 과일 이름이 하나씩 찍혀요. "
           "그럼 처음 질문으로 돌아가서, 이 블록에서는 무엇을 하나씩 보면 될까요?")
CLAIM = "0보다 큰 값만 골라서 더해요"  # 블록의 답(자기 생각)
REASK = "for 문 쓰는 법을 알려 주세요"  # 물음 꼴이 아닌 되묻기
UNCLEAR = "0보다 큰 값만 더하면 되는 건가요?"  # 물음 꼴로 낸 자기 생각
JUDGED = {"주장": "[check]Y t", "물음 꼴 생각": "[check]Y t", "코드": "[check]Y t", "딴말": "[check]O"}  # 말 은행의 답(규칙 밖)에 줄 판정


def talked(mode, ctx, text, judge, reply=EXPLAIN):
    return fakes.go(fakes.make_state("turn", ctx, mode=mode, event="message", text=text), {f"{mode}.judge": [judge], ASK[mode]: [reply]})


def chain(mode, ctx, steps):
    """steps: (요청 꾸리기, 대본, 채점 함수). 턴마다 저장될 말을 대화에 붙여 다음 턴으로 넘긴다."""
    out = []
    for make, scripts, check in steps:
        done, fake = fakes.go(make(ctx), scripts, check)
        assert done.get("error") is None, done.get("error")
        ctx, rows = saved(done, mode)
        out.append((done, fake, rows))
    return out, ctx


def scene_context(mode, key):
    """말 은행 장면의 첫 블록이 지금 블록이고, 그 블록의 첫 질문까지 나온 대화."""
    s = bank.SCENES[key]
    blocks = [Block(id="b1", kind=s["kind"], name=s["name"], goal=s["goal"], reference=s["reference"], checks=list(s["checks"]), hints=list(s["hints"])),
              Block(id="b2", kind="var_during", name=s["next"], goal=f"목표-{s['next']}", reference=s["next_reference"])]
    return fakes.context(problem_text=s["problem"], language=s["language"], plan=fakes.planned(blocks), open_count=1,
                         **{mode: [fakes.service(s["hints"][0], 0, "s0", OPENING[mode])]})


class QuestionTurnTest(unittest.TestCase):
    """판정이 Q(되묻는 말)일 때. 두 방식 × 블록 자리마다."""

    def test_q_explains_and_keeps_progress(self):
        """설명은 모델 1회(판정 1 + 생성 1). 진행·블록 확인은 그대로, 그 말과 답은 튜터 말의 블록 번호를 잇고, 다음 '모르겠어요'는 힌트 2번이다."""
        for mode in ("chair", "guide"):
            for i in range(N):
                with self.subTest(mode=mode, block=i + 1):
                    ctx = context(mode, i)
                    done, fake = talked(mode, ctx, GRAMMAR, "[check]Q")
                    self.assertIsNone(done.get("error"))
                    result = done["result"]
                    self.assertEqual((done["open_count"], result["advance"], result["move"]), (i + 1, False, "term"))
                    self.assertEqual(fakes.tasks(fake), [f"{mode}.judge", ASK[mode]])
                    self.assertEqual((done.get("block_check"), done.get("block_fixes"), result["reply"]), (None, None, EXPLAIN))
                    after, rows = saved(done, mode)
                    asked_about = getattr(ctx, mode)[-1].block_index
                    self.assertEqual([r["block_index"] for r in rows], [asked_about, asked_about])
                    if mode == "chair":
                        self.assertEqual(shown_count(after, mode), i)  # 이름이 드러나지 않는다
                    later, fake2 = fakes.go(said(mode, "모르겠어요")(after), {})
                    self.assertEqual((later["result"]["reply"], later["open_count"], fake2.calls), (HINTS[i][1], i + 1, []))

    def test_q_after_a_pass_points_at_the_opened_block(self):
        """블록 → 말: 코드 확인 통과로 다음 블록이 열린 뒤 그 첫 질문을 되물었다. 답은 열린 블록 번호를 잇고 진행은 그대로다."""
        for mode in ("chair", "guide"):
            for i in range(N - 1):
                with self.subTest(mode=mode, block=i + 1):
                    out, _ = chain(mode, context(mode, i), [(checked(mode, i, PASS), {}, exec_check([], CASES)),
                                                            (said(mode, "그게 무슨 말이에요?"), {f"{mode}.judge": ["[check]Q"], ASK[mode]: [EXPLAIN]}, None),
                                                            (said(mode, "모르겠어요"), {}, None)])
                    (passed, _, rows1), (asked, fake, rows2), (stuck, _, _) = out
                    self.assertEqual((passed["open_count"], rows1[-1]["block_index"]), (i + 2, i + 1))
                    self.assertEqual((asked["open_count"], asked["result"]["advance"], asked["result"]["move"]), (i + 2, False, "term"))
                    self.assertEqual(fakes.tasks(fake), [f"{mode}.judge", ASK[mode]])
                    self.assertEqual([r["block_index"] for r in rows2], [i + 1, i + 1])
                    self.assertEqual((stuck["open_count"], stuck["result"]["reply"]), (i + 2, HINTS[i + 1][1]))

    def test_w_is_taken_like_q(self):
        """지금의 W(낱말 뜻)는 Q와 같게 받는다: 진행, 차례, 호출, 말, 생성 지시가 같다."""
        def outcome(mode, judge):
            done, fake = talked(mode, context(mode, 1), "누적이 무슨 뜻이에요?", judge)
            return done["open_count"], done["result"]["advance"], done["result"]["move"], fakes.tasks(fake), done["result"]["reply"], fakes.prompt(fake, ASK[mode])

        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                self.assertEqual(outcome(mode, "[check]Q"), outcome(mode, "[check]W"))
                self.assertEqual(outcome(mode, "[check]Q")[2], "term")

    def test_q_prompt_answers_the_words_and_returns(self):
        """생성 지시에는 사용자가 되물은 말, 돌아갈 원래 질문, 그 차례의 지시가 있다. 답 요청·무관한 말로 다루지 않는다."""
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                _, fake = talked(mode, context(mode, 1), GRAMMAR, "[check]Q")
                text = fakes.prompt(fake, ASK[mode])
                for part in (GRAMMAR, HINTS[1][0], STEPS[mode]["term"]):
                    self.assertIn(part, text)
                self.assertNotIn("답을 달라고 했다", text)
                self.assertNotIn("무관한 말을 했다", text)

    def test_explanation_does_not_leak_block_code(self):
        """문법 설명에 이 블록의 참고 코드 줄이 섞이면 그 말은 나가지 않는다(기존 답 노출 검사)."""
        for mode in ("chair", "guide"):
            for i in range(N):
                line = BLOCKS[i].reference.splitlines()[-1].strip()
                with self.subTest(mode=mode, block=i + 1, line=line):
                    done, _ = talked(mode, context(mode, i), GRAMMAR, "[check]Q", f"`{line}`처럼 쓰면 돼요. 그럼 이어서 무엇을 적을까요?")
                    self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"]), (i + 1, False, "term"))
                    self.assertNotIn(line, done["result"]["reply"])


class MisjudgedTest(unittest.TestCase):
    """잘못 갈랐을 때. 어느 쪽으로 잘못 갈라도 말로는 다음 블록이 열리지 않는다."""

    def test_answer_taken_as_question_explains_without_progress(self):
        """답인데 Q로 봄: 튜터가 설명하고 진행은 없다."""
        for mode in ("chair", "guide"):
            for i in range(N):
                with self.subTest(mode=mode, block=i + 1):
                    done, fake = talked(mode, context(mode, i), CLAIM, "[check]Q")
                    self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"], done["result"]["reply"]), (i + 1, False, "term", EXPLAIN))
                    self.assertEqual(len(fake.calls), 2)
                    self.assertIsNone(done.get("block_check"))

    def test_question_taken_as_answer_never_opens(self):
        """되묻기인데 답으로 봄: N이면 질문이 돌아오고, Y면 코드로 적으라는 고정 말이고 넘기지 않는다."""
        for mode in ("chair", "guide"):
            for i in range(N):
                with self.subTest(mode=mode, block=i + 1):
                    no, fake = talked(mode, context(mode, i), REASK, "[check]N1", ASKED)
                    self.assertEqual((no["open_count"], no["result"]["advance"], no["result"]["reply"], len(fake.calls)), (i + 1, False, ASKED, 2))
                    yes, fake = talked(mode, context(mode, i), REASK, "[check]Y t")
                    self.assertEqual((yes["open_count"], yes["result"]["advance"], yes["result"]["move"], len(fake.calls)), (i + 1, False, "write", 1))
                    self.assertTrue(is_write(i, yes["result"]["reply"]), yes["result"]["reply"])

    def test_unclear_question_with_y_asks_to_check(self):
        """애매함(물음 꼴 + Y): 맞다고 말하지 않고 스스로 확인하게 묻는다. 넘기지 않는다."""
        for mode in ("chair", "guide"):
            for i in range(N):
                with self.subTest(mode=mode, block=i + 1):
                    done, fake = talked(mode, context(mode, i), UNCLEAR, "[check]Y t", ASKED)
                    self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"], done["result"]["reply"]), (i + 1, False, "verify", ASKED))
                    self.assertEqual(fakes.tasks(fake), [f"{mode}.judge", ASK[mode]])


class JudgeRuleTest(unittest.TestCase):
    def test_parse_q_like_w(self):
        q, w = parse_verdict("[check]Q"), parse_verdict("[check]W")
        self.assertIsNotNone(q)
        self.assertEqual((q.ok, q.aside), (w.ok, w.aside))
        self.assertTrue(q.aside)

    def test_judge_prompt_defines_q(self):
        """판정 지시에 Q의 뜻이 있다: 자기 생각이 아니라 튜터 말·문제·문법·개념을 되묻는 말이다."""
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                _, fake = talked(mode, context(mode, 1), GRAMMAR, "[check]Q")
                rule = "\n".join(line for line in fakes.prompt(fake, f"{mode}.judge").splitlines() if "[check]Q" in line)
                self.assertTrue(rule)
                for word in ("튜터", "문제", "문법", "개념", "자기 생각"):
                    self.assertIn(word, rule)

    def test_term_step_carries_grammar_rules(self):
        """되묻는 말 차례의 지시: 문법은 이 문제와 상관없는 작은 예로 답하고, 이 블록의 답은 말하지 않고, 원래 질문으로 돌아온다."""
        for mode, steps in STEPS.items():
            with self.subTest(mode=mode):
                for word in ("문법", "상관없는", "답", "돌아"):
                    self.assertIn(word, steps["term"])


class TalkBankTest(unittest.TestCase):
    """말 은행 120개(되묻기 60, 답 60)."""

    def test_bank_shape(self):
        texts = [row[0] for row in bank.BANK]
        self.assertEqual(len(texts), len(set(texts)))
        for label, kinds, each in ((bank.ASK, bank.ASK_KINDS, 12), (bank.SAY, bank.SAY_KINDS, 10)):
            for kind in kinds:
                rows = [text for text, lab, k, _ in bank.BANK if k == kind]
                self.assertEqual(len(rows), each, kind)
                self.assertTrue(all(lab == label for _, lab, k, _ in bank.BANK if k == kind), kind)
                if label == bank.ASK:  # 물음표가 있는 말과 없는 말이 섞였다
                    self.assertGreaterEqual(sum("?" in text for text in rows), 3, kind)
                    self.assertGreaterEqual(sum("?" not in text for text in rows), 3, kind)
        for text, _, kind, scene in bank.BANK:
            self.assertIn(scene, bank.SCENES)
            if kind == "물음 꼴 생각":
                self.assertTrue(asks(text), text)
            if kind == "주장":
                self.assertFalse(asks(text), text)

    def test_rules_take_only_empty_and_answer_requests(self):
        """규칙 층: 내용 없는 말과 답 요청만 규칙이 가른다. 되묻는 말은 모두 판정으로 넘긴다."""
        for text, label, kind, _ in bank.BANK:
            with self.subTest(text=text):
                got = rule_verdict(text)
                if kind in bank.RULE_KINDS:
                    self.assertIsNotNone(got)
                    self.assertEqual((got.ok, got.aside), (False, bank.RULE_KINDS[kind]))
                else:
                    self.assertIsNone(got)

    def test_bank_never_opens_and_questions_get_explained(self):
        """그래프 층: 말 은행의 어느 말도 블록을 열지 않는다. 되묻기(Q)는 설명 차례, 규칙이 가른 말은 모델 0회."""
        for mode in ("chair", "guide"):
            for text, label, kind, scene in bank.BANK:
                with self.subTest(mode=mode, text=text):
                    judge = "[check]Q" if label == bank.ASK else JUDGED.get(kind)
                    scripts = {**({f"{mode}.judge": [judge]} if judge else {}), ASK[mode]: ["작은 예로 먼저 볼게요. 처음 질문으로 돌아가면 무엇을 정해야 할까요?"]}
                    done, fake = fakes.go(fakes.make_state("turn", scene_context(mode, scene), mode=mode, event="message", text=text), scripts)
                    self.assertIsNone(done.get("error"))
                    self.assertEqual((done["open_count"], done["result"]["advance"], done.get("block_check")), (1, False, None))
                    if label == bank.ASK:
                        self.assertEqual((done["result"]["move"], fakes.tasks(fake)), ("term", [f"{mode}.judge", ASK[mode]]))
                    elif kind in bank.RULE_KINDS:
                        self.assertEqual(fake.calls, [])
                    else:
                        self.assertNotEqual(done["result"]["move"], "term")


class TermLeakTest(unittest.TestCase):
    """되묻기 답(term)의 결정적 검사. 이 문제 코드가 만든 이름을 쓴 코드, 참고 코드 줄과 공백만 다른 코드, 의자에서 찾기 전 지금 블록 이름은 대체 질문으로 바뀐다.
    상관없는 이름으로 쓴 문법 예는 언어마다 그대로 나간다(예약어·형·가져오기 줄만 같은 예). 어느 쪽이든 호출은 판정 1 + 생성 1이고 진행과 힌트 번호는 그대로다."""

    LEAKS = [("plus", "`for x in items`처럼 쓰면 값을 하나씩 꺼내요. 그럼 처음 질문으로 돌아가서, 무엇을 하나씩 볼까요?"),
             ("plus", "`if x>0:`처럼 쓰면 조건을 걸 수 있어요. 그럼 언제 합에 더해야 할까요?"),
             ("plus", "`total+=x`처럼 쓰면 값을 더해요. 그럼 언제 더해야 할까요?"),
             ("plus", "`for n in items:`처럼 쓰면 값을 하나씩 꺼내요. 그럼 무엇을 하나씩 볼까요?"),
             ("plus", "`items[0]`처럼 쓰면 첫 값을 꺼내요. 그럼 무엇을 하나씩 볼까요?"),
             ("shelf", "`count[t] = count.get(t, 0) + 1`처럼 쓰면 개수를 셀 수 있어요. 그럼 제목마다 무엇을 기록해 둘까요?"),
             ("shelf", "seen[t] = count.get(t, 0) + 1 처럼 쓰면 개수를 셀 수 있어요. 그럼 제목마다 무엇을 기록해 둘까요?")]  # 백틱 없는 대입 줄
    NAMED = "지금은 양수만 더하기 블록이니 하나씩 보는 문법부터 볼게요. 그럼 items의 값을 어떻게 하나씩 볼까요?"
    STARTERS = {"plus": "def solution(items):\n    answer = 0\n    return answer", "shelf": "def solution(loans, k):\n    answer = []\n    return answer"}
    # 양수만 더하기 장면을 언어마다 옮긴 것: (시작 코드, 지금 블록 참고 코드, 상관없는 문법 예)
    LANGS = {
        "python": ("def solution(items):\n    answer = 0\n    return answer", "    for x in items:\n        if x > 0:\n            total += x",
                   ["`for fruit in fruits:`", "`for x in fruits:`", "`import math`"]),
        "java": ("class Solution {\n    public int solution(int[] items) {\n        int answer = 0;\n        return answer;\n    }\n}",
                 "        int total = 0;\n        for (int x : items) {\n            if (x > 0) total += x;\n        }",
                 ["`int[] marks = new int[3];`", "`import java.util.*;`", "`for (int i = 0; i < marks.length; i++) {`"]),
        "javascript": ("function solution(items) {\n    let answer = 0;\n    return answer;\n}",
                       "    let total = 0;\n    for (const x of items) {\n        if (x > 0) total += x;\n    }",
                       ["`function add(a, b) {`", "`const fruits = [];`", "`for (const fruit of fruits) {`"]),
        "cpp": ("#include <vector>\nusing namespace std;\n\nint solution(vector<int> items) {\n    int answer = 0;\n    return answer;\n}",
                "    int total = 0;\n    for (int x : items) {\n        if (x > 0) total += x;\n    }",
                ["`#include <string>`", "`max(a, b)`", "`sort(marks.begin(), marks.end());`"]),
        "rust": ("fn solution(items: Vec<i32>) -> i32 {\n    let answer = 0;\n    answer\n}",
                 "    let mut total = 0;\n    for x in items {\n        if x > 0 { total += x; }\n    }",
                 ["`let score: i32 = 90;`", "`fn add(a: i32, b: i32) -> i32 {`", "`use std::collections::HashMap;`", "`x as usize`"]),
    }
    TAIL = "처럼 쓰면 돼요. 그럼 처음 질문으로 돌아가서, items의 값을 어떻게 하나씩 볼까요?"

    def scene(self, mode, scene, language=None):
        """말 은행 장면에 시작 코드를 붙인 문맥(진입 함수의 인자가 이 문제의 이름이다). language를 주면 지금 블록 코드를 그 언어로 바꾼다."""
        ctx = scene_context(mode, scene)
        if language is None:
            return replace(ctx, starter=self.STARTERS[scene])
        starter, reference, _ = self.LANGS[language]
        plan = fakes.planned([replace(ctx.plan.blocks[0], reference=reference), *ctx.plan.blocks[1:]])
        return replace(ctx, language=language, starter=starter, plan=plan)

    def turn(self, mode, ctx, reply, scene="plus"):
        """[check]Q 뒤 말 만들기 답을 넣는다. 나간 말을 돌려주고, 호출·진행과 다음 '모르겠어요'의 힌트 번호를 본다."""
        done, fake = talked(mode, ctx, GRAMMAR, "[check]Q", reply)
        self.assertEqual((done["result"]["move"], done["result"]["advance"], done["open_count"], fakes.tasks(fake)),
                         ("term", False, 1, [f"{mode}.judge", ASK[mode]]))
        later, fake2 = fakes.go(said(mode, "모르겠어요")(saved(done, mode)[0]), {})
        self.assertEqual((later["result"]["reply"], later["open_count"], fake2.calls), (bank.SCENES[scene]["hints"][1], 1, []))
        return done["result"]["reply"]

    def test_problem_code_falls_back(self):
        from ..common.talk_rules import FALLBACK

        for mode in ("chair", "guide"):
            for scene, reply in self.LEAKS:
                with self.subTest(mode=mode, reply=reply):
                    self.assertEqual(self.turn(mode, self.scene(mode, scene), reply, scene), FALLBACK["term"])
            for language in self.LANGS:  # 진입 함수의 인자를 쓴 코드는 언어마다 막힌다
                with self.subTest(mode=mode, language=language):
                    self.assertEqual(self.turn(mode, self.scene(mode, "plus", language), "`items[0]`" + self.TAIL), FALLBACK["term"])

    def test_unfound_block_name_falls_back_only_in_chair(self):
        from ..common.talk_rules import FALLBACK

        self.assertEqual(self.turn("chair", self.scene("chair", "plus"), self.NAMED), FALLBACK["term"])  # 의자: 지금 블록 이름은 찾을 답이다
        self.assertEqual(self.turn("guide", self.scene("guide", "plus"), self.NAMED), self.NAMED)  # 가이드: 지금 블록 이름은 이미 보인다

    def test_unrelated_example_goes_out(self):
        for mode in ("chair", "guide"):
            for language, (_, _, examples) in self.LANGS.items():
                for example in examples:
                    with self.subTest(mode=mode, language=language, example=example):
                        self.assertEqual(self.turn(mode, self.scene(mode, "plus", language), example + self.TAIL), example + self.TAIL)

    def test_term_step_hides_current_block_name_in_chair(self):
        self.assertIn("지금 블록 이름", CHAIR_STEPS["term"])


@unittest.skipUnless(os.environ.get("ALGOBLOCK_LIVE") == "1", "ALGOBLOCK_LIVE=1일 때만")
class LiveTalkBankTest(unittest.TestCase):
    def test_misjudged_share(self):
        """실제 판정 모델로 말 은행을 가른다(방식은 번갈아). 되묻기를 답으로 본 비율과 답을 되묻기로 본 비율이 상한 안이다."""
        missed = {bank.ASK: [], bank.SAY: []}
        for k, (text, label, kind, scene) in enumerate(bank.BANK):
            mode = ("chair", "guide")[k % 2]
            done = run(fakes.make_state("turn", scene_context(mode, scene), mode=mode, event="message", text=text), store=None, compiled=fakes.pipeline())
            if (getattr(done.get("move"), "move", None) == "term") != (label == bank.ASK):
                missed[label].append(f"{mode} {kind}: {text}")
        total = {label: sum(row[1] == label for row in bank.BANK) for label in missed}
        print("\n".join(["잘못 가른 말:", *missed[bank.ASK], *missed[bank.SAY]]))
        self.assertLessEqual(len(missed[bank.ASK]) / total[bank.ASK], bank.ASK_AS_SAY_MAX)
        self.assertLessEqual(len(missed[bank.SAY]) / total[bank.SAY], bank.SAY_AS_ASK_MAX)


if __name__ == "__main__":
    unittest.main()
