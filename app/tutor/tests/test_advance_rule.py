"""블록 진행 규칙(그래프 전체, 가짜 모델). 다음 블록은 지금 블록을 끝냈을 때만 열린다.
끝냈다는 것은 블록 코드 확인 통과, 넘어가기, 끝까지 내 방식으로, 채우기 가운데 하나다. 어느 방식에서든 말로는 열리지 않는다."""

import textwrap
import unittest
from dataclasses import replace

from . import fakes
from .test_pipeline import exec_check
from ..common.talk_rules import ALL_FILLED, ANSWER_LEAD, OWN_WAY, RETRY_LEAD, SKIPPED
from ..llm import LlmTimeout
from ..save.nodes import collect
from ..save.respond import shown_count
from ..state import BlockState, ChatMessage
from ..turn.code_check import code_hash
from ..turn.moves import FOUND_OK, WRITE_TIP, WRITE_TIP_LAST

PROBLEM = "정수 배열 items가 주어집니다. 0보다 큰 값만 모두 더한 합을 return 하도록 solution 함수를 완성하세요."
HINTS = [["합을 담을 이름은 무엇으로 시작할까요?", "더한 값을 어디에 모아 둘까요?", "items가 [3, -1, 2]라면 처음 합은 얼마일까요?"],
         ["items의 값을 어떻게 하나씩 볼까요?", "'0보다 큰 값만'을 보면 언제 더해야 할까요?", "-1을 만나면 합은 어떻게 될까요?"],
         ["다 본 뒤에는 무엇을 돌려줄까요?", "모은 합은 어디에 있나요?", "[3, -1, 2]의 답은 얼마일까요?"]]
BLOCKS = [fakes.block(1, "합 준비", "def solution(items):\n    total = 0", checks=["합을 0에서 시작한다"], hints=HINTS[0]),
          fakes.block(2, "양수만 더하기", "    for x in items:\n        if x > 0:\n            total += x", "loop",
                      checks=["하나씩 본다", "0보다 큰 값만 더한다"], hints=HINTS[1]),
          fakes.block(3, "합 돌려주기", "    return total", "var_during", checks=["모은 합을 돌려준다"], hints=HINTS[2])]
N = len(BLOCKS)
CASES = [([[3, -1, 2]], 5), ([[-5]], 0), ([[1, 1]], 2)]
PASS = ["def solution(items):\n    total = int()", "    for x in items:\n        total += max(x, 0)", "    return total + 0"]  # 계획 코드와 글자가 달라 실행해 본다
FAIL = ["def solution(items):\n    total = 1", "    for x in items:\n        total += x", "    return -total"]
ASKED = "[3, -1, 2]에서 -1을 만나면 합은 어떻게 될까요?"
BASIS = "'0보다 큰 값만 더한다'는 생각은 문제 글의 어느 문장에서 나왔나요?"
OPENING = {"chair": "open", "guide": "blank"}
ASK = {"chair": "chair.ask", "guide": "guide.lead"}


def unrun(problem_id, code, quick=False):
    return {"status": "toolchain_missing", "cases": []}


def never(*args, **kwargs):
    raise AssertionError("실행하지 않는 사건이다")


def context(mode, i, chat=None, **extra):
    """i번째 블록(0부터)이 지금 블록이고, 그 블록의 첫 질문까지 나온 대화."""
    talk = [fakes.service(HINTS[i][0], i, "s0", OPENING[mode])] if chat is None else chat
    return fakes.context(problem_text=PROBLEM, spec="정수 배열 하나, 합 하나", plan=fakes.planned(BLOCKS), open_count=i + 1, **{mode: talk}, **extra)


def after_basis(mode, i):
    return [fakes.service(HINTS[i][0], i, "s0", "open"), fakes.user("0보다 큰 값만 더해요", i, "u0"), fakes.service(BASIS, i, "s1", "basis")]


def talk(text, judge=None, ask=None):
    def make(mode, i, ctx):
        scripts = {**({f"{mode}.judge": [judge]} if judge else {}), **({ASK[mode]: [ask]} if ask else {})}
        return fakes.make_state("turn", ctx, mode=mode, event="message", text=text), scripts, None
    return make


def code(pick, check=None, back=0, **extra):
    """back: 지금 블록보다 몇 칸 앞 블록을 확인받는가. 모델 판정이 필요한 칸은 거절(N1)과 질문 하나를 받는다."""
    def make(mode, i, ctx):
        j = i - back
        state = fakes.make_state("turn", ctx, mode=mode, event="block_filled", block_id=BLOCKS[j].id, code=pick[j], **extra)
        return state, {f"{mode}.check_code": ["[check]N1"], ASK[mode]: [ASKED]}, check or exec_check([], CASES)
    return make


def said(mode, text):
    return lambda ctx: fakes.make_state("turn", ctx, mode=mode, event="message", text=text)


def checked(mode, j, pick):
    return lambda ctx: fakes.make_state("turn", ctx, mode=mode, event="block_filled", block_id=BLOCKS[j].id, code=pick[j])


def fill(mode, i, ctx):
    return fakes.make_state("fill", ctx, block_id=BLOCKS[i].id), {}, exec_check([], CASES)


def saved(done, mode):
    """저장 단계(N1 collect)가 남길 줄과, 그 줄을 대화에 이어 붙이고 진행을 옮긴 다음 턴의 문맥."""
    rows = collect(done)["changes"]["messages"]
    lines = [ChatMessage(id=f"n{len(getattr(done['ctx'], mode))}-{k}", role=r["role"], text=r["text"], at=r["at"], block_index=r["block_index"], move=r["move"])
             for k, r in enumerate(rows)]
    ctx = done["ctx"]
    states = dict(ctx.block_states)
    for item in [done.get("block_check"), *(done.get("block_fixes") or [])]:
        if item is not None:
            states[item.block_id] = item
    return replace(ctx, open_count=done["open_count"], block_states=states, **{mode: getattr(ctx, mode) + lines}), rows


def is_write(i, reply):
    return reply == (WRITE_TIP_LAST if i == N - 1 else WRITE_TIP)


def next_hint(i, reply):
    return reply.endswith(HINTS[i + 1][0])


SAME, NEXT, ALL = "그대로", "하나 엶", "모두 엶"
YES, NO = "지금 블록까지", "앞 블록까지"  # 의자에서 이름이 보이는 블록

# 진행 행렬. 블록 자리는 첫·가운데·끝, 방식은 의자·가이드. None은 그 방식에 없는 사건이거나 단언하지 않는 칸이다.
MATRIX = [
    # 사건                 만드는 법                                                               넘김   열린 블록  차례(의자, 가이드)       모델 호출  의자 이름  말
    ("말 Y 평서",          talk("0보다 큰 값만 골라서 더해요", "[check]Y t"),                       False, SAME, ("write", "write"),   (1, 1),    YES,  is_write),
    ("말 Y 물음",          talk("0보다 큰 값만 골라서 더하면 되나요?", "[check]Y t", ASKED),        False, SAME, ("verify", "verify"), (2, 2),    NO,   lambda i, r: r == ASKED),
    ("말 N",               talk("한 번씩 다 더하면 될 것 같아요", "[check]N1", ASKED),              False, SAME, ("assume", "tool"),   (2, 2),    NO,   lambda i, r: r == ASKED),
    ("내용 없는 말",       talk("모르겠어요"),                                                      False, SAME, ("clue", "tool"),     (0, 0),    NO,   lambda i, r: r == HINTS[i][1]),
    ("답 요청",            talk("그냥 답 코드 알려 줘"),                                            False, SAME, ("clue", "tool"),     (0, 0),    NO,   lambda i, r: r == HINTS[i][1] + "\n" + ANSWER_LEAD.strip()),
    ("근거 질문 뒤 평서",  talk("문제에 0보다 큰 값만 더한다고 적혀 있어서요"),                     False, SAME, ("write", None),      (0, None), YES,  is_write),
    ("근거 질문 뒤 물음",  talk("문제 글에 그렇게 적혀 있지 않나요?", "[check]Y t", ASKED),          False, SAME, ("verify", None),     (2, None), NO,   lambda i, r: r == ASKED),
    ("코드 통과",          code(PASS),                                                              True,  NEXT, ("open", "blank"),    (0, 0),    YES,  next_hint),
    ("코드 실패",          code(FAIL),                                                              False, SAME, ("clue", "tool"),     (0, 0),    NO,   lambda i, r: r.startswith(RETRY_LEAD) and r.endswith(HINTS[i][1])),
    ("실행 못 함",         code(FAIL, unrun),                                                       False, SAME, ("clue", "tool"),     (1, 1),    NO,   lambda i, r: r.startswith("이 블록은 실행하지 못해서(")),
    ("넘어가기",           code(FAIL, never, quiet=True, skip=True),                                True,  NEXT, ("open", "blank"),    (0, 0),    YES,  lambda i, r: r.startswith(SKIPPED) and next_hint(i, r)),
    ("끝까지 내 방식으로", code(FAIL, never, quiet=True, skip=True, own_way=True),                  True,  ALL,  ("done", "done"),     (0, 0),    None, lambda i, r: r == SKIPPED + "\n" + OWN_WAY),
    ("채우기",             fill,                                                                    None,  NEXT, (None, None),      (0, 0),    YES,  None),
    ("앞 블록 다시 확인",  code(PASS, back=1),                                                      False, SAME, ("done", "done"),     (0, 0),    NO,   lambda i, r: r.startswith(FOUND_OK)),
]

# 끝 블록에서 기대가 다른 칸: 다음 블록이 없다. 가이드는 끝 안내(질문 없음, 모델 0회), 의자는 처음부터 되짚는 정리 질문(모델 1회).
LAST = {
    ("코드 통과", "guide"): {"move": "done", "reply": lambda i, r: r == ALL_FILLED and "?" not in r},
    ("코드 통과", "chair"): {"move": "recap", "calls": 1, "reply": lambda i, r: r == ASKED},
    ("넘어가기", "guide"): {"move": "done", "reply": lambda i, r: r.startswith(SKIPPED)},
    ("넘어가기", "chair"): {"move": "recap", "calls": 1, "reply": None},
    ("채우기", "chair"): {"named": None},
}


class AdvanceMatrixTest(unittest.TestCase):
    """방식 2 × 블록 자리 3 × 사건마다 넘김, 열린 블록 수, 차례 이름, 모델 호출 수, 이름 드러남, 저장되는 블록 번호."""

    def test_matrix(self):
        for mode in ("chair", "guide"):
            for i in range(N):
                for event, make, advance, opens, moves, calls, named, reply in MATRIX:
                    if (event.startswith("근거") and mode == "guide") or (event == "앞 블록 다시 확인" and i == 0):
                        continue  # 가이드는 근거를 묻지 않는다. 첫 블록에는 앞 블록이 없다
                    k = 0 if mode == "chair" else 1
                    want = {"move": moves[k], "calls": calls[k], "named": named, "reply": reply, **(LAST.get((event, mode), {}) if i == N - 1 else {})}
                    with self.subTest(mode=mode, block=i + 1, event=event):
                        ctx = context(mode, i, after_basis(mode, i) if event.startswith("근거") else None)
                        self.cell(mode, i, ctx, *make(mode, i, ctx), advance, opens, want)

    def cell(self, mode, i, ctx, state, scripts, check, advance, opens, want):
        before = ctx.open_count
        done, fake = fakes.go(state, scripts, check)
        self.assertIsNone(done.get("error"))
        after, result = done["open_count"], done["result"]
        self.assertEqual(after, {SAME: before, NEXT: min(before + 1, N), ALL: N}[opens])
        self.assertTrue(1 <= before <= after <= N)  # 1 이상 블록 수 이하이고 줄지 않는다
        if want["calls"] is not None:
            self.assertEqual(len(fake.calls), want["calls"], fakes.tasks(fake))
        if state["request"].event == "message":  # 사건이 말이면 진행도 블록 확인 상태도 바뀌지 않는다
            self.assertEqual((after, result["advance"], done.get("block_check"), done.get("block_fixes")), (before, False, None, None))
        if state["request"].kind == "fill":
            self.assertEqual(done["block_check"].verdict, "Y")
            self.assertIn(result["code"], textwrap.dedent(BLOCKS[i].reference))  # 그 블록의 코드(틀 줄은 빠질 수 있다)
        else:
            self.assertEqual((result["advance"], result["move"]), (advance, want["move"]))
            if want["reply"] is not None:
                self.assertTrue(want["reply"](i, result["reply"]), result["reply"])
            for later in BLOCKS[after:]:  # 잠긴 블록 이름은 말에 나오지 않는다
                self.assertNotIn(later.name, result["reply"])
        ctx_after, rows = saved(done, mode)
        if rows:
            target = rows[-1]["block_index"]
            self.assertTrue(0 <= target < after, (target, after))  # 그 말이 겨눈 블록은 열린 블록 안이다
            if advance and opens == NEXT and i < N - 1:  # 끝낸 블록 다음 블록의 첫 힌트가 그 블록 번호로 저장된다
                self.assertEqual((target, rows[-1]["text"].endswith(HINTS[i + 1][0])), (i + 1, True))
        shown = shown_count(ctx_after, mode)  # 다음 턴 응답에서 이름이 보이는 블록 수
        if mode == "guide":
            self.assertEqual(shown, after)
        elif want["named"] is not None:
            self.assertEqual(shown, i + 1 if want["named"] == YES else i)


class AdvanceRegressionTest(unittest.TestCase):
    """말로 다음 블록이 열리던 길(의자)과 그 둘레, 두 걸음 연속(말 → 블록, 블록 → 말)."""

    def go_chain(self, mode, ctx, steps):
        """steps: (요청 꾸리기, 대본, 채점 함수). 턴마다 저장될 말을 대화에 붙여 다음 턴으로 넘긴다."""
        out = []
        for make, scripts, check in steps:
            state = make(ctx)
            done, fake = fakes.go(state, scripts, check)
            self.assertIsNone(done.get("error"))
            ctx, rows = saved(done, mode)
            out.append((done, fake, rows))
        return out, ctx

    def test_question_with_right_idea_does_not_open(self):
        """의자, 변수 블록, 판정 Y(짐작)인 물음. 블록 1에 대한 확인 질문이 오고 열리지 않는다."""
        ctx = fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1, chair=[fakes.service(fakes.HINTS1[0], 0)])
        asked = "owl, tide, owl이면 owl은 몇 번 세어질까요?"
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="chair", event="message", text="제목마다 개수를 세면 되나요?"),
                              {"chair.judge": ["[check]Y g"], "chair.ask": [asked]})
        self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"], done["move"].target), (1, False, "verify", 0))
        self.assertEqual((fakes.tasks(fake), done["result"]["reply"]), (["chair.judge", "chair.ask"], asked))
        self.assertNotIn("found", done["result"])

    def test_term_question_after_basis_does_not_open(self):
        """의자, 조건 블록. Y → 근거 질문 → '근거가 무슨 뜻이에요?'. 판정을 거쳐 뜻을 풀고, 근거 질문을 볼 수 있게 넘긴다. 열리지 않는다."""
        talk_so_far = [fakes.service(fakes.HINTS1[0], 0, "m1"), fakes.user("이름을 세면 돼요", 0), fakes.service(BASIS, 0, "m2", "basis")]
        ctx = fakes.context(plan=fakes.planned(fakes.thinking()), open_count=1, chair=talk_so_far)
        said = "근거는 그렇게 생각한 까닭이에요. 예를 들어 우산을 챙긴 근거는 일기 예보일 수 있어요. 그럼 그 생각은 문제 글의 어느 문장에서 나왔나요?"
        done, fake = fakes.go(fakes.make_state("turn", ctx, mode="chair", event="message", text="근거가 무슨 뜻이에요?"),
                              {"chair.judge": ["[check]W"], "chair.ask": [said]})
        self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"], done["move"].target), (1, False, "term", 0))
        self.assertEqual(fakes.tasks(fake), ["chair.judge", "chair.ask"])
        self.assertIn(BASIS, fakes.prompt(fake, "chair.ask"))  # 돌아갈 근거 질문이 지시에 있다

    def test_said_then_checked_opens_with_next_hint(self):
        """말 → 블록: 말로 맞힌 블록은 이름과 코드 칸이 열리고, 그 칸의 코드 확인이 통과해야 다음 블록이 열린다.
        다음 블록의 첫 힌트는 다음 블록 번호로 저장되고 모델은 부르지 않는다."""
        for mode in ("chair", "guide"):
            for i in range(N - 1):
                with self.subTest(mode=mode, block=i + 1):
                    out, ctx = self.go_chain(mode, context(mode, i), [(said(mode, "0보다 큰 값만 골라서 더해요"), {f"{mode}.judge": ["[check]Y t"]}, None),
                                                                      (checked(mode, i, PASS), {}, exec_check([], CASES))])
                    (first, _, rows1), (second, fake2, rows2) = out
                    self.assertEqual((first["open_count"], first["result"]["move"], rows1[-1]["block_index"]), (i + 1, "write", i))
                    self.assertEqual(shown_count(second["ctx"], mode), i + 1)  # 말로 맞힌 블록은 이름이 보인다
                    self.assertEqual((second["open_count"], second["result"]["advance"], fake2.calls), (i + 2, True, []))
                    self.assertEqual((rows2[-1]["block_index"], rows2[-1]["text"].endswith(HINTS[i + 1][0])), (i + 1, True))
                    self.assertEqual(shown_count(ctx, mode), i + 1 if mode == "chair" else i + 2)  # 의자: 다음 블록 이름은 다시 가린다

    def test_check_then_talk_points_at_that_block(self):
        """블록 → 말: 확인 뒤의 말에 튜터가 답할 때 그 확인 결과와 그 블록을 본다. 실패면 같은 블록, 통과면 열린 다음 블록."""
        for mode in ("chair", "guide"):
            for i in range(N - 1):
                for pick, target, seen in ((FAIL, i, "기대한 값은 5인데"), (PASS, i + 1, HINTS[i + 1][0])):
                    with self.subTest(mode=mode, block=i + 1, passed=pick is PASS):
                        out, _ = self.go_chain(mode, context(mode, i), [(checked(mode, i, pick), {}, exec_check([], CASES)),
                                                                        (said(mode, "한 번씩 다 더하면 될 것 같아요"), {f"{mode}.judge": ["[check]N1"], ASK[mode]: [ASKED]}, None)])
                        (check, _, _), (answered, fake, rows) = out
                        self.assertIn(seen, check["result"]["reply"])
                        self.assertEqual((answered["open_count"], answered["result"]["advance"], rows[-1]["block_index"]), (check["open_count"], False, target))
                        self.assertIn(seen, fakes.prompt(fake, ASK[mode]))  # 튜터의 다음 말을 짓는 지시에 방금 확인한 결과(또는 열린 블록의 첫 질문)가 있다

    def test_same_statement_twice_never_opens(self):
        """같은 말을 거듭 보내도 진행은 그대로다(두 번 보내기를 막는 잠금은 서버 시험이 본다)."""
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                step = (said(mode, "0보다 큰 값만 골라서 더해요"), {f"{mode}.judge": ["[check]Y t"]}, None)
                out, ctx = self.go_chain(mode, context(mode, 0), [step, step])
                self.assertEqual([d["open_count"] for d, _, _ in out], [1, 1])
                self.assertEqual(ctx.block_states, {})

    def test_fixing_an_earlier_block_keeps_progress_and_stales_later(self):
        """블록 3까지 열린 뒤 블록 1을 틀리게 고쳐 확인하면 통과가 아니고, 뒤의 통과한 블록은 '확인 전'으로 돌아가고, 진행은 그대로다."""
        states = {"b1": BlockState("b1", PASS[0], code_hash(PASS[0]), "Y"), "b2": BlockState("b2", PASS[1], code_hash(PASS[1]), "Y")}
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                ctx = context(mode, N - 1, block_states=states)
                done, fake = fakes.go(checked(mode, 0, FAIL)(ctx), {}, exec_check([], CASES))
                self.assertEqual((done["open_count"], done["result"]["advance"], fake.calls, done["move"].target), (N, False, [], 0))
                self.assertNotEqual(done["block_check"].verdict, "Y")
                self.assertEqual([(f.block_id, f.verdict) for f in done["block_fixes"]], [("b2", "?")])

    def test_talk_after_the_last_block_stays_in_range(self):
        """마지막 블록을 끝낸 뒤의 말은 마무리 말이고 블록 번호가 넘치지 않는다(모델 0회)."""
        for mode, last in (("chair", "recap"), ("guide", "done")):
            with self.subTest(mode=mode):
                chat = [fakes.service(HINTS[2][0], 2, "s0", OPENING[mode]), fakes.user(PASS[2], 2, "u0"), fakes.service(ASKED if mode == "chair" else ALL_FILLED, 2, "s1", last)]
                done, fake = fakes.go(said(mode, "합을 0에서 시작해서 양수만 더하고 돌려줘요")(context(mode, N - 1, chat)), {f"{mode}.judge": ["[check]Y t"], ASK[mode]: [ASKED]})
                self.assertEqual((done["open_count"], done["result"]["advance"], done["result"]["move"], fake.calls), (N, False, "close", []))
                self.assertTrue(0 <= done["move"].target < N)

    def test_same_recheck_is_recorded_once(self):
        """앞 블록을 같은 코드로 다시 확인하면 같은 말이라 대화에 다시 쌓지 않는다. 진행은 그대로다."""
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                step = (checked(mode, 0, PASS), {}, exec_check([], CASES))
                out, ctx = self.go_chain(mode, context(mode, 1), [step, step])
                (first, _, rows1), (second, _, rows2) = out
                self.assertEqual((len(rows1), rows2, collect(second)["result"].get("repeated")), (2, [], True))
                self.assertEqual([d["open_count"] for d, _, _ in out], [2, 2])

    def test_model_failure_keeps_progress(self):
        """모델이 실패하면 오류이고 진행도 저장할 것도 없다."""
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, _ = fakes.go(said(mode, "한 번씩 다 더하면 될 것 같아요")(context(mode, 1)), {f"{mode}.judge": ["[check]N1"], ASK[mode]: [LlmTimeout("늦음")]})
                self.assertEqual((done["error"].code, done["open_count"], done.get("response")), ("llm_timeout", 2, None))


if __name__ == "__main__":
    unittest.main()
