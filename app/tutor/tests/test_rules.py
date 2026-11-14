"""규칙(모델 없음): 전략, 블록 검사, 힌트 다듬기, 해설 절, 나가는 글 검사, 열린 블록 수, 판정 읽기, 대화 원칙, 피드백 검사, 요청 거절."""

import unittest
from dataclasses import replace

from . import fakes
from ..common.assess import pick_strategy
from ..common.scope import ALGORITHMS
from ..common.talk_rules import BANNED, banned_in, quotes_ok, reply_problems
from ..common.verdict import parse_verdict
from ..explain.rules import check_sections
from ..feedback.rules import check_feedback, mark_claims
from ..output_check.nodes import guard, progress, strip_fence
from ..plan.rules import check_blocks, clean_blocks
from ..state import EXPLAIN_TITLES, ChatMessage, Explain, Section


class StrategyTest(unittest.TestCase):
    def test_table(self):
        self.assertEqual(pick_strategy(False, None, None), "fresh")
        self.assertEqual(pick_strategy(False, 80, True), "fresh")
        self.assertEqual(pick_strategy(True, 49, True), "canonical")
        self.assertEqual(pick_strategy(True, 50, True), "keep_flow")
        self.assertEqual(pick_strategy(True, 80, False), "canonical")
        self.assertEqual(pick_strategy(True, None, None), "canonical")
        self.assertEqual(pick_strategy(True, 100, True), "keep_flow")


class BlockRuleTest(unittest.TestCase):
    def test_rejects_empty_unknown_and_duplicate(self):
        self.assertEqual(check_blocks([], "hash").message, "블록이 없습니다.")
        self.assertEqual(check_blocks([fakes.block(1, "이름", "코드", kind="sort")], "hash").message, "블록 종류가 아닙니다.")
        self.assertEqual(check_blocks([fakes.block(1, "  ", "코드")], "hash").code, "invalid_output")
        one, dup = fakes.block(1, "이름", "코드"), fakes.block(1, "다른", "코드2")
        self.assertEqual(check_blocks([one, dup], "hash").message, "블록 식별자가 겹칩니다.")
        self.assertIsNone(check_blocks(fakes.two(), "hash"))

    def test_algorithm_must_be_one_of_ten(self):
        self.assertEqual(len(ALGORITHMS), 15)  # 기본 문제의 주제 15개와 같다(ui/problems/README.md)
        for key in (*ALGORITHMS, "dfs_bfs"):  # dfs_bfs는 예전 계획에 남은 유형이라 계속 받아 준다
            self.assertIsNone(check_blocks(fakes.two(), key), key)
        for bad in ("", "floyd", "구현", "HASH"):
            self.assertEqual(check_blocks(fakes.two(), bad).message, "풀이 유형이 아닙니다.")

    def test_clean_hints(self):
        good = fakes.hinted()
        cleaned = clean_blocks(good, fakes.PROBLEM)
        self.assertEqual(cleaned[0].hints, fakes.HINTS1)
        self.assertEqual(cleaned[1].hints, fakes.HINTS2)
        cases = {
            "금지 표현": ["좋아요! 무엇을 기록할까요?", fakes.HINTS1[1], fakes.HINTS1[2]],
            "질문 아님": ["명단을 기록하세요.", fakes.HINTS1[1], fakes.HINTS1[2]],
            "뒤 블록 이름": ["NEXT_SECRET 전에 무엇을 할까요?", fakes.HINTS1[1], fakes.HINTS1[2]],
            "지어낸 인용": [fakes.HINTS1[0], "'글자는 모두 다르다'를 보면 어떨까요?", fakes.HINTS1[2]],
            "코드 펜스": [fakes.HINTS1[0], fakes.HINTS1[1], "```x```로 해 볼까요?"],
            "참고 코드": [fakes.HINTS1[0], fakes.HINTS1[1], "REF_ONE을 쓰면 어떨까요?"],
        }
        for why, hints in cases.items():
            with self.subTest(why=why):
                broken = [replace(good[0], hints=hints), good[1]]
                self.assertEqual(clean_blocks(broken, fakes.PROBLEM)[0].hints, [])
                self.assertEqual(clean_blocks(broken, fakes.PROBLEM)[1].hints, fakes.HINTS2)
        capped = clean_blocks([replace(good[0], checks=["a", "b", "c", "d", " "], hints=fakes.HINTS1 + ["넷째 질문인가요?"])], fakes.PROBLEM)[0]
        self.assertEqual((len(capped.checks), len(capped.hints)), (3, 3))


class SectionRuleTest(unittest.TestCase):
    def test_order_and_blank(self):
        self.assertIsNone(check_sections(Explain([Section(t, "본문") for t in EXPLAIN_TITLES])))
        swapped = [Section(EXPLAIN_TITLES[1], "x"), Section(EXPLAIN_TITLES[0], "x"), Section(EXPLAIN_TITLES[2], "x"), Section(EXPLAIN_TITLES[3], "x")]
        self.assertIsNone(check_sections(Explain(swapped)))  # 고정 제목이 섞여 오면 제목 순서대로 다시 놓는다
        self.assertEqual([s.title for s in swapped], list(EXPLAIN_TITLES))
        renamed = [Section(f"절{i}", "x") for i in range(4)]
        self.assertIsNone(check_sections(Explain(renamed)))  # 네 절이면 자리대로 고정 제목
        self.assertEqual(check_sections(Explain(renamed[:3])).message, "해설 절 순서가 아닙니다.")
        blank = [Section(t, "  " if i == 2 else "x") for i, t in enumerate(EXPLAIN_TITLES)]
        self.assertEqual(check_sections(Explain(blank)).message, "해설 절이 비었습니다.")


class OutputCheckTest(unittest.TestCase):
    def state(self, kind, **kwargs):
        return fakes.make_state(kind, fakes.context(plan=fakes.planned(fakes.two()), open_count=1), **kwargs)

    def test_guard(self):
        chair = self.state("turn", mode="chair", event="message", text="응")
        chair["result"] = {"reply": "여기 ``` 코드", "advance": False}
        self.assertEqual(guard(chair)["error"].message, "말풍선에 코드 펜스가 있습니다.")
        explained = self.state("explain")
        explained["result"] = {"explain": "본문 ```python\n코드\n```"}
        self.assertIsNone(guard(explained).get("error"))
        hinted = self.state("feedback")
        hinted["result"] = {"similar_hint": "흐름 ```"}
        self.assertEqual(guard(hinted)["error"].message, "힌트에 코드 펜스가 있습니다.")
        filled = self.state("fill", block_id="b1")
        filled["result"] = {"code": "```python\nprint(1)\n```"}
        self.assertEqual(guard(filled)["result"]["code"], "print(1)")
        self.assertEqual(strip_fence("그대로"), "그대로")
        empty = self.state("fill", block_id="b1")
        empty["result"] = {"code": "```\n```"}
        self.assertEqual(guard(empty)["error"].message, "블록 코드가 비었습니다.")
        follow = self.state("followup", mode="chair", quote_id="m1", text="왜")
        follow["result"] = {"reply": "이유?", "advance": True}
        self.assertNotIn("advance", guard(follow)["result"])

    def test_progress(self):
        plan = fakes.planned(fakes.two())
        fresh = fakes.make_state("explain", fakes.context())
        fresh.update(plan=plan, result={})
        self.assertEqual(progress(fresh)["open_count"], 1)
        rows = [
            ("turn", 1, {"advance": True}, {}, 2),
            ("turn", 1, {"advance": False}, {}, 1),
            ("turn", 2, {"advance": True}, {}, 2),
            ("fill", 1, {"code": "x"}, {"block_id": "b1"}, 2),
            ("fill", 2, {"code": "x"}, {"block_id": "b1"}, 2),
            ("fill", 2, {"code": "x"}, {"block_id": "b2"}, 2),
        ]
        for kind, count, result, extra, want in rows:
            with self.subTest(kind=kind, count=count, result=result):
                state = fakes.make_state(kind, fakes.context(plan=plan, open_count=count), mode="chair", event="message", **extra)
                state["result"] = result
                self.assertEqual(progress(state)["open_count"], want)
        self.assertEqual(progress(fakes.make_state("turn", fakes.context(open_count=0)))["open_count"], 0)


class VerdictTest(unittest.TestCase):
    def test_parse(self):
        self.assertTrue(parse_verdict("[check]Y").ok)
        got = parse_verdict("판정: [check]N2 끝")
        self.assertEqual((got.ok, got.miss, got.basis), (False, 2, None))
        got = parse_verdict("[check]Y g")
        self.assertEqual((got.ok, got.basis), (True, "g"))
        got = parse_verdict("[check]N1 t")
        self.assertEqual((got.miss, got.basis), (1, "t"))
        self.assertEqual(parse_verdict("[check]72 Y").score, 72)
        self.assertFalse(parse_verdict("[check] n").ok)
        self.assertEqual(parse_verdict("[check]Y e입니다").basis, "e")
        for bad in ("Y", "[check]", None):
            self.assertIsNone(parse_verdict(bad))


class TalkRuleTest(unittest.TestCase):
    def test_banned_skips_problem_quotes(self):
        problem = "정답을 return 하세요. 당연히 이름은 소문자입니다."
        self.assertEqual(banned_in("'정답을 return 하세요'는 무엇을 돌려 달라는 뜻일까요?", problem), [])
        self.assertEqual(banned_in("정답이에요! 다음은요?", problem), ["정답"])
        self.assertIn("좋아요", BANNED)

    def test_quotes(self):
        self.assertTrue(quotes_ok("'제목이 같으면 같은 책입니다'를 보면요?", fakes.PROBLEM))
        self.assertTrue(quotes_ok("'제목이같으면같은책입니다'를 보면요?", fakes.PROBLEM))  # 공백은 보지 않는다
        self.assertFalse(quotes_ok("'모두 다른 이름이다'를 보면요?", fakes.PROBLEM))
        self.assertTrue(quotes_ok("인용 없이 묻는다면?", fakes.PROBLEM))

    def test_reply_problems(self):
        ok = reply_problems("같은 이름이 두 번 나오면 그 방법으로도 남은 사람이 보일까요?", move="assume", problem=fakes.PROBLEM)
        self.assertEqual(ok, [])
        bad = reply_problems("좋은 생각이에요. 다음은 NEXT_SECRET이에요.", move="open", problem=fakes.PROBLEM, later_names=["NEXT_SECRET"])
        self.assertEqual(set(bad), {"금지 표현", "동의로 시작", "질문으로 끝나지 않음", "뒤 블록 이름"})
        many = "하나. 둘. 셋. 넷인가요?"
        self.assertIn("3문장 초과", reply_problems(many, move="open", problem=""))
        self.assertIn("참고 코드", reply_problems("count[p] += 1 을 쓰면 될까요?", move="open", problem="", reference="count[p] += 1"))
        self.assertIn("문제 글에 없는 인용", reply_problems("'없는 문장'은 무슨 뜻일까요?", move="clue", problem=fakes.PROBLEM))
        self.assertEqual(reply_problems("", move="open", problem=""), ["비었음"])

    def test_agree_opener(self):
        """원칙 1: 첫 문장 맨 앞의 동의·칭찬 여는 말만 본다. 이음말·앞말은 검사 뒤에 붙고, 문항 글 인용은 뺀다."""
        for text in ("맞아요, 그러면 다음은?", "네, 같은 이름이 두 번이면요?", "그렇죠. 그다음은 무엇을 셀까요?", "바로 그거예요. 다음은?", "정확합니다! 다음은?"):
            self.assertIn("동의로 시작", reply_problems(text, move="open", problem=""), text)
        for text in ("다음 블록을 열었어요. 이 블록에서 무엇을 정해야 할까요?", "그 방법이 맞아 보이는 까닭은 무엇일까요?", "네 번째 이름은 어떻게 될까요?"):
            self.assertNotIn("동의로 시작", reply_problems(text, move="open", problem=""), text)
        problem = "좋습니다를 출력한다."
        self.assertEqual(reply_problems("'좋습니다를 출력한다'는 언제 출력하라는 걸까요?", move="clue", problem=problem), [])


class FeedbackRuleTest(unittest.TestCase):
    def test_marks_and_hint_head(self):
        marked = mark_claims("집합으로 바꾸면 둘이 하나가 되지 않을까요? [확실] 제출은 실패다. 같은 글자가 합쳐진다.")
        self.assertEqual(marked, "집합으로 바꾸면 둘이 하나가 되지 않을까요? [확실] 제출은 실패다. [추측] 같은 글자가 합쳐진다.")
        fields, error = check_feedback("질문일까요? 잘했어요 거의 됐다.", "개수로 센다", "정석 순서로", "해시")
        self.assertIsNone(error)
        self.assertEqual(fields["similar_hint"], "해시: 개수로 센다")
        self.assertNotIn("잘했어요", fields["analysis"])
        self.assertTrue(fields["analysis"].split("? ", 1)[1].startswith("[추측]"))
        self.assertEqual(check_feedback("a?", "```x```", "b", "해시")[1].code, "invalid_output")
        self.assertEqual(check_feedback("a?", "해시: 센다", "b", "해시")[0]["similar_hint"], "해시: 센다")

    def test_marks_follow_sentence_endings(self):
        marked = mark_claims("[확실] 같은 시각에 둘이 내릴까요? [추측] 같은 결과가 나올 가능성이 높습니다. "
                             "[확실] 시간 안에 끝날 것으로 보입니다. 블록 순서대로 구현되어 있습니다.")
        self.assertEqual(marked, "같은 시각에 둘이 내릴까요? [가능성 높음] 같은 결과가 나올 가능성이 높습니다. "
                                 "[추측] 시간 안에 끝날 것으로 보입니다. [추측] 블록 순서대로 구현되어 있습니다.")
        self.assertEqual(mark_claims("[확실] 제출은 실패다. [확실]"), "[확실] 제출은 실패다.")  # 끝에 표시만 남지 않는다


class RequestCheckTest(unittest.TestCase):
    def test_rejections_do_not_call_llm(self):
        plan = fakes.planned(fakes.two())
        user_line = ChatMessage(id="user1", role="user", text="사용자말", at="t", block_index=0)
        cases = [
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1), mode="explain", event="start"), "validation"),
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1), mode="chair", event="nope"), "validation"),
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1), mode="chair", event="message", text="  "), "validation"),
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1), mode="chair", event="block_filled", block_id="b2", code="x"), "validation"),
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1), mode="chair", event="block_filled", block_id="b1", code=" "), "validation"),
            (fakes.make_state("turn", fakes.context(plan=plan, open_count=1, chair=[fakes.service("이미?", 0)]), mode="chair", event="start"), "already_started"),
            (fakes.make_state("followup", fakes.context(plan=plan, open_count=1, chair=[fakes.service("말?", 0)]), mode="chair", quote_id="없는", text="왜"), "not_found"),
            (fakes.make_state("followup", fakes.context(plan=plan, open_count=1, chair=[user_line]), mode="chair", quote_id="user1", text="왜"), "not_found"),
            (fakes.make_state("followup", fakes.context(plan=plan, open_count=1), mode="chair", quote_id="", text="왜"), "validation"),
            (fakes.make_state("fill", fakes.context(), block_id="b1"), "block_not_found"),
            (fakes.make_state("fill", fakes.context(plan=plan, open_count=1), block_id="없는"), "block_not_found"),
            (fakes.make_state("fill", fakes.context(plan=plan, open_count=1), block_id="b2"), "block_closed"),
            (fakes.make_state("feedback", fakes.context(plan=plan, open_count=1)), "not_submitted"),
            (fakes.make_state("nope", fakes.context()), "validation"),
        ]
        for state, code in cases:
            with self.subTest(code=code, request=state["request"]):
                done, fake = fakes.go(state, {})
                self.assertEqual(done["error"].code, code)
                self.assertEqual(fake.calls, [])


class ReplyLeakRuleTest(unittest.TestCase):
    """실제로 나간 적이 있는 말풍선(모델 메모, 영어 지시문, 잘못 인용)을 막는다."""

    def test_model_notes_and_english_are_rejected(self):
        from ..common.talk_rules import reply_problems

        note = "세어서 비교하는 쪽으로 기울었으니, 작은 예시로 따라가 보게 하자. 원소 3개짜리 예시는 무엇일까요?"
        self.assertIn("3인칭 메모", reply_problems(note, move="trace", problem=fakes.PROBLEM))
        english = "Pick out the first thing the user said that the answer can hinge on: 무엇일까요?"
        self.assertIn("영어 지시문", reply_problems(english, move="assume", problem=fakes.PROBLEM))

    def test_quotes_user_words_ok_problem_misquote_not(self):
        from ..common.talk_rules import reply_problems

        said = "이름을 세면 돼요"
        self.assertEqual(reply_problems("'이름을 세면 된다'는 생각은 어디서 나왔나요?", move="basis", problem=fakes.PROBLEM, said=said), [])
        self.assertIn("문제 글에 없는 인용", reply_problems("'가장 많이 나온 글자'을 보면 무엇을 셀까요?", move="open", problem=fakes.PROBLEM, said=said))
        self.assertEqual(reply_problems("'(]'처럼 짝이 다르면 어떻게 될까요?", move="trace", problem=fakes.PROBLEM), [])  # 예시 값


class RepairTest(unittest.TestCase):
    def test_repair_unquotes_cuts_and_trims(self):
        from ..common.talk_rules import repair, reply_problems

        text = "'가장 많이 나온 글자'을 보면 무엇을 셀까요? 천천히 생각해 봐요."
        fixed = repair(text, fakes.PROBLEM)
        self.assertEqual(fixed, "가장 많이 나온 글자을 보면 무엇을 셀까요?")
        self.assertEqual(reply_problems(fixed, move="open", problem=fakes.PROBLEM), [])
        self.assertEqual(repair("하나. 둘. 셋. 넷은요?", fakes.PROBLEM), "둘. 셋. 넷은요?")

    def test_repair_keeps_quotes_in_code(self):
        from ..common.talk_rules import repair

        for text in ("fruits = deque(['사과', '배', '포도'])처럼 써요. 맨 앞은 어떻게 뺄까요?",
                     "`fruits.popleft('사과')`처럼 써요. '없는 말'을 보면 어떻게 될까요?"):
            fixed = repair(text, fakes.PROBLEM)
            self.assertIn("'사과'", fixed)
        self.assertIn(" 없는 말을 보면", fixed)  # 문장 속 근거 없는 따옴표는 지금처럼 벗긴다

    def test_echo_opener_is_dropped_when_a_question_follows(self):
        """평가에서 걸린 되받기 첫 문장(뒤 질문은 줄였다)."""
        from ..common.talk_rules import repair

        asks = {
            "점심을 라면으로 할지 고민하고 계시군요.": "벨트 위 무게는 언제 줄어들까요?",
            "줄에 남은 상자가 있는 동안 한 바퀴를 1초로 보고 계속 돌면 된다는 생각이시군요.": "이 생각은 문제 글이나 예시에서 나온 것인가요, 아니면 짐작인가요?",
            "나중에 연 괄호가 먼저 닫힌다는 점과, 스택 크기로 지금 깊이를 안다는 점을 말해 주셨어요.": "가장 깊은 깊이는 어떤 값에서 시작해야 할까요?",
            "12번째 줄에서 load가 8이고 4를 더해 12가 되는 상황을 짚었어요.": "그때 limit과 견주면 어떻게 되나요?",
            "덱의 맨 앞을 꺼내는 문법을 물으셨네요.": "과일 덱에서 맨 앞을 빼면 무엇이 남을까요?",  # 실제 모델 확인에서 나온 꼴
        }
        for echo, ask in asks.items():
            self.assertEqual(repair(f"{echo} {ask}", fakes.PROBLEM), ask)
        self.assertEqual(repair("이름을 센다는 생각이시군요.", fakes.PROBLEM), "이름을 센다는 생각이시군요.")  # 남는 질문이 없으면 그대로


class VerdictOtherTest(unittest.TestCase):
    def test_d_is_other_direction(self):
        from ..common.verdict import parse_verdict

        got = parse_verdict("[check]D g")
        self.assertEqual((got.ok, got.other, got.basis), (False, True, "g"))
        self.assertFalse(parse_verdict("[check]N1 t").other)


class OneQuestionTest(unittest.TestCase):
    def test_extra_questions_are_dropped_keeping_statements(self):
        from ..common.talk_rules import one_question, question_count, repair, reply_problems

        text = "sara를 적을 자리를 정해 보실래요? 예시는 [\"sara\", \"mina\"]예요. 한 칸에 횟수를 적으면 다시 찾기 쉬울까요?"
        self.assertEqual(question_count(text), 2)
        self.assertIn("질문 여럿", reply_problems(text, move="trace", problem=fakes.PROBLEM))
        self.assertEqual(one_question(text), "예시는 [\"sara\", \"mina\"]예요. 한 칸에 횟수를 적으면 다시 찾기 쉬울까요?")
        self.assertEqual(reply_problems(repair(text, fakes.PROBLEM), move="trace", problem=fakes.PROBLEM), [])
        joined = "벨트 위 무게 합은 얼마로 둘까요? 0초가 되기 직전이라고 생각해 봅시다. 아니면 무게 합만 먼저 고르시겠어요?"
        self.assertEqual(repair(joined, fakes.PROBLEM), "0초가 되기 직전이라고 생각해 봅시다. 무게 합만 먼저 고르시겠어요?")
        quoted = "'for문으로 보면 되나요?'라고 하셨는데, [1, 3, 1]에서도 될까요?"  # 인용 안의 물음표는 질문이 아니다
        self.assertEqual(question_count(quoted), 1)


JAVA_SUM = """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int n = Integer.parseInt(br.readLine().trim());
        StringTokenizer st = new StringTokenizer(br.readLine());
        long sum = 0;
        for (int i = 0; i < n; i++) {
            sum += Long.parseLong(st.nextToken());
        }
        System.out.println(sum);
    }
}"""


class FrameTest(unittest.TestCase):
    """블록 칸의 글을 한 파일로 모으기(composed_parts: 블록 코드 확인과 같은 framed). 화면에는 틀 정보를 싣지 않는다."""

    def test_python_and_java_frames(self):
        from ..common.solution import composed_parts
        from ..save.respond import session_body

        py = [fakes.block(1, "세기", "def solution(s):\n    count = {}"), fakes.block(2, "돌기", "    for c in s:\n        count[c] = 1", "loop")]
        body = session_body(fakes.context(plan=fakes.planned(py), open_count=1))
        self.assertFalse({"indent", "head", "tail", "unit", "braces", "outer"} & set(body["blocks"][0]))  # 화면은 틀 정보를 쓰지 않는다
        self.assertEqual(composed_parts(py, {"b1": {"code": "count = {}"}, "b2": {"code": "for c in s:\n    count[c] = 1"}}, "python"),
                         [[0, "def solution(s):\n    # 블록 1 · var_from_problem\n    count = {}"], [1, "    # 블록 2 · loop\n    for c in s:\n        count[c] = 1"]])
        java = [fakes.block(1, "준비", "import java.util.*;\n\nclass Solution {\n    public int solution(String s) {\n        int depth = 0;"),
                fakes.block(2, "돌기", "        for (char c : s.toCharArray()) {\n            depth++;\n        }", "loop"),
                fakes.block(3, "답", "        return depth;\n    }\n}")]
        self.assertEqual(composed_parts(java, {"b1": {"code": "int depth = 0;"}, "b2": {"code": " "}, "b3": {"code": "return depth;"}}, "java", ["준비", "돌기", "답"]),
                         [[0, "import java.util.*;\n\nclass Solution {\n    public int solution(String s) {\n        // 블록 1 · 준비\n        int depth = 0;"],
                          [2, "        // 블록 3 · 답\n        return depth;\n    }\n}"]])  # 빈 블록은 빠진다
        helper = [fakes.block(1, "도우미", "def drop_old(heap, left):\n    return heap")]  # 도우미 함수 머리는 풀이의 일부다
        self.assertEqual(composed_parts(helper, {"b1": {"code": "def drop_old(heap, left):\n    return heap"}}, "python"),
                         [[0, "# 블록 1 · var_from_problem\ndef drop_old(heap, left):\n    return heap"]])

    def test_program_mode_skeleton_is_frame(self):
        """표준 입출력 문제: import·main 머리·맨 끝 main() 호출·닫는 괄호는 틀 줄이다. 알맹이만 적어도 같은 코드로 본다(피드백의 같은 코드 세기).
        방식은 코드 모양으로 짐작하지 않고 넘겨받는다(program)."""
        from ..common.solution import composed_parts, same_code

        py = [fakes.block(1, "읽기", "import sys\ninput = sys.stdin.readline\n\ndef main():\n    n = int(input())"),
              fakes.block(2, "돌기", "    best = 1\n    for i in range(n):\n        best += 1", "loop"),
              fakes.block(3, "출력", "    print(best)\n\nmain()")]
        parts = composed_parts(py, {"b1": {"code": "n = int(input())"}, "b3": {"code": "print(best)"}}, "python", program=True)
        self.assertEqual(parts, [[0, "import sys\ninput = sys.stdin.readline\n\ndef main():\n    # 블록 1 · var_from_problem\n    n = int(input())"],
                                 [2, "    # 블록 3 · var_from_problem\n    print(best)\n\nmain()"]])
        self.assertTrue(same_code("print(best)", py[2].reference, "python"))
        self.assertTrue(same_code("n = int(input())", py[0].reference, "python"))
        java = [fakes.block(1, "읽기", "import java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n"
                                       "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        int n = Integer.parseInt(br.readLine().trim());"),
                fakes.block(2, "출력", "        System.out.println(n);\n    }\n}")]
        parts = composed_parts(java, {"b1": {"code": "int n = 1;"}, "b2": {"code": "System.out.println(n);"}}, "java", program=True)
        self.assertIn("    public static void main(String[] args) throws IOException {\n        // 블록 1", parts[0][1])
        self.assertTrue(parts[1][1].endswith("        System.out.println(n);\n    }\n}"), parts[1][1])
        self.assertTrue(same_code("BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\nint n = Integer.parseInt(br.readLine().trim());",
                                  java[0].reference, "java"))
        self.assertTrue(same_code("System.out.println(n);", java[1].reference, "java"))
        self.assertTrue(same_code("cout << n;", "    cout << n;\n    return 0;\n}", "cpp", program=True))
        self.assertFalse(same_code("cout << n;", "    cout << n;\n    return 0;\n}", "cpp"))  # 함수 방식에서는 return 0도 답이다

    def test_tail_closes_only_the_skeleton(self):
        """반복문으로 끝나는 블록의 '}'가 tail로 실려 중괄호 없이 적은 for 뒤에 덧붙어 컴파일 오류가 났다.
        tail에는 뼈대(진입 클래스·main)를 닫는 '}'만, 블록 맨 앞의 '}'(앞 블록에서 연 것)는 알맹이다."""
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path

        from ..common.solution import frame_of, spliced

        rows = JAVA_SUM.splitlines()
        refs = ["\n".join(rows[:7]), "\n".join(rows[7:12]), "\n".join(rows[12:])]
        self.assertEqual(frame_of(refs[0], "java", True)["head"], rows[:5])
        self.assertEqual({k: v for k, v in frame_of(refs[1], "java", True).items() if k in ("indent", "head", "tail", "outer", "braces")},
                         {"indent": 8, "head": [], "tail": [], "outer": [], "braces": 0})  # 반복문을 닫는 '}'는 알맹이
        self.assertEqual(frame_of(refs[2], "java", True)["tail"], ["    }", "}"])
        self.assertEqual(frame_of("        }\n        System.out.println(sum);\n    }\n}", "java", True)["head"], [])
        mine = "StringTokenizer st = new StringTokenizer(br.readLine());\nlong sum = 0;\nfor (int i = 0; i < n; i++) sum += Long.parseLong(st.nextToken());"
        program = spliced(refs, 1, mine, "java")
        self.assertIn("        for (int i = 0; i < n; i++) sum += Long.parseLong(st.nextToken());\n        System.out.println(sum);\n    }\n}", program)
        self.assertEqual(program.count("}"), 2)
        if shutil.which("javac"):
            with tempfile.TemporaryDirectory() as folder:
                Path(folder, "Main.java").write_text(program)
                done = subprocess.run(["javac", "Main.java"], cwd=folder, capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)


class KindRuleTest(unittest.TestCase):
    def test_block_starting_with_loop_becomes_loop(self):
        blocks = [fakes.block(1, "돌기", "    # 하나씩\n    for x in a:\n        n += 1", "condition"),
                  fakes.block(2, "고르기", "    if n > 3:\n        n = 3", "condition"),
                  fakes.block(3, "돌기", "        while (left < right) {", "branch")]
        self.assertEqual([b.kind for b in clean_blocks(blocks[:2], fakes.PROBLEM)], ["loop", "condition"])  # 다른 종류는 모델 것을 둔다
        self.assertEqual(clean_blocks(blocks[2:], fakes.PROBLEM, "java")[0].kind, "loop")


class RenamedCodeTest(unittest.TestCase):
    def test_only_names_differ_is_same_code(self):
        """'conveyor = deque()'를 거부하고 'belt = deque()'는 통과했다. 대입한 이름만 다르면 모델 없이 통과한다."""
        from ..common.solution import same_code

        self.assertTrue(same_code("conveyor = deque()", "    belt = deque()", "python"))
        self.assertTrue(same_code("for ch in s:\n    seen[ch] = 1", "    for c in s:\n        seen[c] = 1", "python"))
        self.assertTrue(same_code("for (int j = 0; j < n; j++) {", "        for (int i = 0; i < n; i++) {", "java"))
        self.assertFalse(same_code("total = max(a)", "total = sum(a)", "python"))  # 다른 내장 함수
        self.assertFalse(same_code("total = sum(b)", "total = sum(a)", "python"))  # 대입하지 않은 이름(앞 블록의 것)은 그대로 본다
        self.assertFalse(same_code('print(x, end=" ")', 'print(x, sep=" ")', "python"))  # 키워드 인자는 이름이 아니다
        self.assertFalse(same_code("x, y = x, x + y", "a, b = b, a + b", "python"))


def _rows(text: str) -> list[str]:
    return [row for row in text.splitlines() if row.strip()]


class OuterLineTest(unittest.TestCase):
    """반복 몸통(8칸)에서 시작해 반복 밖(4칸)에서 끝나는 블록은 어떻게 적어도 바깥 줄을 놓을 수 없었고, 평평하게 적은 계획 코드는 통과했다."""

    REF = "        res.append(left)\n    return res"

    def test_first_line_is_the_anchor(self):
        from ..common.solution import frame_of, framed

        self.assertEqual(frame_of(self.REF, "python")["outer"], [4])
        for mine in ("    res.append(left)\nreturn res", "        res.append(left)\n    return res", "  res.append(left)\nreturn res"):  # 상대·절대·2칸
            self.assertEqual(framed(mine, self.REF, "python"), self.REF, mine)
        self.assertEqual(framed("res.append(left)\nreturn res", self.REF, "python"), "        res.append(left)\n        return res")  # 평평한 꼴은 둘 다 안
        deep = "            if x:\n                y = 1\n        z = 2\n    return z"  # 바깥 단계 둘: 가까운 것부터
        self.assertEqual(framed("    if x:\n        y = 1\n  z = 2\nreturn z", deep, "python"), deep)
        self.assertEqual(framed("    a = 1\nb = 2", "    a = 1\n    b = 2", "python"), "    a = 1\nb = 2")  # outer가 없으면 첫 줄과의 차만큼 내어 쓴다

    def test_same_code_sees_python_shape(self):
        from ..common.solution import same_code

        self.assertFalse(same_code("res.append(left)\nreturn res", self.REF, "python"))
        self.assertTrue(same_code("  res.append(left)\nreturn res", self.REF, "python"))
        self.assertTrue(same_code("    lst = lst + [left]\nreturn lst", "        res = res + [left]\n    return res\n", "python"))  # 대입한 이름만 다름
        java = "            sum += i;\n        }\n        System.out.println(sum);"
        self.assertTrue(same_code("sum += i;\n}\nSystem.out.println(sum);", java, "java"))  # 중괄호 언어는 들여쓰기를 보지 않는다

    def test_every_builtin_python_plan_round_trips(self):
        """모든 기본 문제의 Python 계획: 블록마다 틀 줄을 떼고 가장 얕은 줄을 0칸으로 내어 쓴 꼴(사용자가 흔히 적는 꼴)과 그 앞 공백을 반으로 줄인 2칸 꼴을
        framed()로 되돌려 이으면 계획 프로그램과 ast.dump가 같다. 블록마다 framed(계획 코드, 계획 코드)와 framed(알맹이, 계획 코드)는
        계획 코드다(빈 줄은 빼고. 튜터가 채운 코드를 그대로 넣어도 꼬리 줄이 겹치지 않는다)."""
        import ast
        import json
        import sys
        from pathlib import Path

        from ..common.solution import frame_flags, frame_of, framed, plan_unit

        path = Path(__file__).resolve().parents[2] / "ui" / "builtin.json"
        if not path.is_file():
            self.skipTest("ui/builtin.json 없음")
        problems = blocks = outer = same = 0
        for row in json.loads(path.read_text(encoding="utf-8")):
            refs = [b["reference"] for b in ((row.get("ready") or {}).get("plan") or {}).get("blocks") or []]
            if not refs or not all(ref.strip() for ref in refs):
                continue
            program, unit = row.get("mode") == "program", plan_unit(refs, "python")
            problems, forms = problems + 1, ([], [])
            for ref in refs:
                rows = ref.splitlines()
                skip = frame_flags(rows, "python", program)
                start = next((i for i, s in enumerate(skip) if not s), len(rows))
                end = next((i for i in range(len(rows) - 1, -1, -1) if not skip[i]), start - 1) + 1
                body = rows[start:end]
                for code in (ref, "\n".join(body)):
                    self.assertEqual(_rows(framed(code, ref, "python", program, unit)), _rows(ref), (row["id"], code))
                cut = min((len(r) - len(r.lstrip()) for r in body if r.strip()), default=0)
                mine = [r[cut:] if r.strip() else "" for r in body]
                half = [" " * ((len(r) - len(r.lstrip())) // 2) + r.lstrip() if r.strip() else "" for r in mine]
                blocks, outer = blocks + 1, outer + bool(frame_of(ref, "python", program)["outer"])
                for joined, typed in zip(forms, (mine, half)):
                    joined.append(framed("\n".join(typed), ref, "python", program, unit) if any(r.strip() for r in typed) else ref)
            want = ast.dump(ast.parse("\n".join(refs)))
            for joined in forms:
                self.assertEqual(ast.dump(ast.parse("\n".join(joined))), want, row["id"])
            same += _rows("\n".join(forms[0])) == _rows("\n".join(refs))
        print(f"\n[기본 문제 전수] 문제 {problems}개, 블록 {blocks}개, 바깥 줄 블록 {outer}개, 글자까지 같은 문제 {same}개", file=sys.stderr)

    def test_tutor_filled_last_block_keeps_one_tail(self):
        """C++ 마지막 블록을 '이 블록 채우기'로 채우면 맨 끝 '}'가 한 번 더 붙어 튜터가 자기 코드를 거부했다. Java는 메서드·클래스를 닫는 '}' 둘."""
        from ..common.solution import frame_of, framed

        cpp = "        res.push_back(e - s);\n    }\n    return res;\n}"
        java = "            sum += x;\n        }\n        System.out.println(sum);\n    }\n}"
        for ref, language, program, body in ((cpp, "cpp", False, 3), (java, "java", True, 3)):
            self.assertEqual(frame_of(ref, language, program)["braces"], -1)
            for code in (ref, "\n".join(ref.splitlines()[:body])):
                self.assertEqual(framed(code, ref, language, program), ref, (language, code))

    def test_my_head_lines_are_not_doubled(self):
        """블록 1에 내 머리말(import + class Main + main 머리)을 적으면 계획 머리말 안에 통째로 들어가 컴파일 오류였다.
        계획 머리 줄에 없는 가져오기 줄만 맨 위에 더하고, 진입 클래스·함수 머리는 계획 것을 쓴다. C++ include도 두 번 나오지 않는다."""
        import shutil
        import subprocess
        import tempfile
        from pathlib import Path

        from ..common.solution import framed, spliced

        rows = JAVA_SUM.splitlines()
        refs = ["\n".join(rows[:7]), "\n".join(rows[7:12]), "\n".join(rows[12:])]
        mine = ("import java.io.BufferedReader;\nimport java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws Exception {\n"
                "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        int n = Integer.parseInt(br.readLine().trim());")
        program = spliced(refs, 0, mine, "java")
        self.assertEqual([program.count(x) for x in ("import java.io.BufferedReader;", "import java.io.*;", "class Main", "void main")], [1, 1, 1, 1])
        self.assertTrue(program.startswith("import java.io.BufferedReader;\nimport java.io.*;"))
        if shutil.which("javac"):
            with tempfile.TemporaryDirectory() as folder:
                Path(folder, "Main.java").write_text(program)
                done = subprocess.run(["javac", "Main.java"], cwd=folder, capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)
        ref = "#include <vector>\n\nusing namespace std;\n\nint solution(vector<int> a) {\n    int total = 0;"
        got = framed("#include <vector>\n#include <bits/stdc++.h>\nusing namespace std;\nint total = 0;", ref, "cpp")
        self.assertEqual(got, "#include <bits/stdc++.h>\n" + ref)
        self.assertEqual(framed("}\nreturn x;", "        }\n        return x;", "cpp"), "        }\n        return x;")  # 앞 블록을 닫는 '}'는 알맹이다

    def test_two_space_block_joins_four_space_plan(self):
        """블록 1을 2칸으로 적으면 통과했지만 4칸인 뒤 블록과 모으면 IndentationError였다."""
        import ast

        from ..common.solution import spliced, swap_names

        refs = ["def first_at_least(values, x):\n    left = 0\n    right = len(values)", "    while left < right:\n        mid = (left + right) // 2",
                "        if values[mid] >= x:\n            right = mid\n        else:\n            left = mid + 1\n    return left",
                "\n\ndef solution(prices, low):\n    return first_at_least(sorted(prices), low)"]
        want = ast.dump(ast.parse("\n".join(refs)))
        got = spliced(refs, 0, "def first_at_least(values, x):\n  left = 0\n  right = len(values)", "python")
        self.assertEqual(ast.dump(ast.parse(got)), want)
        names = {"left": "lo", "right": "hi"}  # 내 이름 + 2칸 꼴의 블록 3(바깥 줄 'return'까지)
        mine = {0: "def first_at_least(values, x):\n  lo = 0\n  hi = len(values)"}
        for code in ("  if values[mid] >= x:\n    hi = mid\n  else:\n    lo = mid + 1\nreturn lo", "\tif values[mid] >= x:\n\t\thi = mid\n\telse:\n\t\tlo = mid + 1\nreturn lo"):
            got = spliced(refs, 2, code, "python", mine, [{}, names, names, names])  # 탭도 한 단계다
            self.assertEqual(ast.dump(ast.parse(got)), ast.dump(ast.parse(swap_names("\n".join(refs), names, "python"))), code)

    def test_swap_names_keeps_plain_strings(self):
        """계획 이름(zone)과 같은 낱말이 문자열 값("zone")으로도 쓰이면, 이름만 바꾸고 값은 둔다. f-문자열 안의 이름은 바꾼다."""
        from ..common.solution import swap_names

        names = {"zone": "place", "words": "parts"}
        self.assertEqual(swap_names('elif words[0] == "zone":\n    print(f"{zone}", \'zone\', zone)', names, "python"),
                         'elif parts[0] == "zone":\n    print(f"{place}", \'zone\', place)')


class LanguageRuleTest(unittest.TestCase):
    """Go 새 이름, 문장인 한도 말, 탭 들여쓰기, 디버그 말의 큰따옴표 인용."""

    def test_go_names_and_tabs(self):
        from ..common.solution import created_names, framed

        self.assertEqual(created_names("for i, p := range parent {\nvar ord []int\nkids := make([][]int, n)\nvar a, b int", "go"),
                         [("i", "loop", ""), ("p", "loop", ""), ("ord", "var", "[]int"), ("kids", "var", ""), ("a", "var", "int"), ("b", "var", "int")])
        ref = "\tchildren := make([][]int, n)\n\tfor f := 0; f < n; f++ {\n\t\tx := f\n\t}"
        self.assertEqual(framed("\tkids := make([][]int, n)\n\tfor f := 0; f < n; f++ {\n\t\tx := f\n\t}", ref, "go"),
                         "\tkids := make([][]int, n)\n\tfor f := 0; f < n; f++ {\n\t\tx := f\n\t}")  # 공백 1칸 + 탭이 섞이지 않는다

    def test_session_tells_checked_code(self):
        """통과한 블록의 코드를 화면에 실어, 칸 글을 고치면 '블록 코드 확인'을 다시 보이게 한다."""
        from ..save.respond import session_body
        from ..state import BlockState

        py = [fakes.block(1, "세기", "def solution(s):\n    count = {}"), fakes.block(2, "돌기", "    for c in s:\n        count[c] = 1", "loop")]
        states = {"b1": BlockState("b1", "cnt = {}", "h", "Y"), "b2": BlockState("b2", "x", "h", "N")}
        rows = session_body(fakes.context(plan=fakes.planned(py), open_count=2, block_states=states), "guide")["blocks"]
        # 넘어가지 못한 블록도 그 글과 판정을 실어 화면이 상태 칩('이어지지 않아요')을 그린다
        self.assertEqual([(row.get("checked"), row.get("verdict")) for row in rows], [("cnt = {}", "Y"), ("x", "N")])

    def test_sentence_error_is_said_as_is(self):
        from ..turn.code_check import seen_line

        case = {"id": "1", "kind": "example", "input": "[[1]]", "expected": "1", "got": "", "status": "runtime_error", "error": "메모리를 너무 많이 써서 멈췄어요"}
        self.assertEqual(seen_line({"cases": [case]}, False), "메모리를 너무 많이 써서 멈췄어요.")  # 한도 말도 '~어요'
        self.assertEqual(seen_line({"cases": [case]}, False, "뒤 블록을 튜터의 코드로 이어 돌리면"), "뒤 블록을 튜터의 코드로 이어 돌리면 메모리를 너무 많이 써서 멈췄어요.")

    def test_debug_double_quote_is_checked(self):
        from ..common.talk_rules import quotes_ok

        self.assertFalse(quotes_ok('그 문장이 "앞 사람 여분을 먼저 확인한다"는 순서와 맞을까요?', fakes.PROBLEM, "", double=True))
        self.assertTrue(quotes_ok('그 문장이 "앞 사람 여분을 먼저 확인한다"는 순서와 맞을까요?', fakes.PROBLEM, ""))  # 의자·가이드는 지금처럼 작은따옴표만


class ModelTalkRuleTest(unittest.TestCase):
    """모델이 지은 말의 되받기·요청 둘, 이름 안내 조사, 줄인 인용."""

    def test_echo_and_two_requests(self):
        from ..common.talk_rules import repair

        said = "정렬 안 하고 그냥 가장 큰 거랑 작은 거 찾으면 안 돼요?"
        answer = "items = [3, 8, 6, 5]처럼 가장 큰 것과 작은 것은 정렬 없이도 빠르게 찾을 수 있어요. 그렇다면 그 두 개를 한 상자에 담은 뒤 남은 물건은 어떻게 하실 건가요?"
        self.assertEqual(repair(f"'{said}'라고 물으셨는데, {answer}", fakes.PROBLEM, said), answer)
        ask = "그 한 개짜리 물건은 어떻게 쓰시겠어요?"
        self.assertEqual(repair(f"10번째 줄 while 조건에서 lo와 hi가 같을 때 반복이 멈추는 지점을 짚으셨네요. {ask}", fakes.PROBLEM), ask)
        two = "정렬은 [7, 7, 7]에서 값을 바꾸지 않으니 lo와 hi를 한 바퀴씩 적어 보세요. 특히 lo가 2가 되어 lo와 hi가 같아지는 순간을 확인해 보면 어떨까요?"
        self.assertEqual(repair(two, fakes.PROBLEM), "lo가 2가 되어 lo와 hi가 같아지는 순간을 확인해 보면 어떨까요?")
        basis = "lo와 hi를 한 바퀴씩 적어 보세요. 그렇게 생각한 까닭이 문제 글에 있나요?"
        self.assertEqual(repair(basis, fakes.PROBLEM, move="basis"), basis)  # 근거 질문은 건드리지 않는다

    def test_six_qa_echo_sentences(self):
        """'…라고 물었어요.', '…고 했어요.', '…제대로 짚었네요.'로 시작한 모델 말(talk_classified.json)."""
        from ..common.talk_rules import repair

        asks = {
            "'정렬 안 하고 그냥 가장 큰 거랑 작은 거 찾으면 안 돼요?'라고 물었어요.": "입력이 [9, 2, 8, 3]이고 capacity가 11일 때, 한 번 고른 뒤 나머지에서 같은 방식으로 다음 짝을 찾으려면 무엇을 다시 훑어야 할까요?",
            "\"반복이 끝나면 지금까지 센 상자 수를 돌려주면 된다\"고 했어요.": "그 말이 맞는지보다 먼저, 반복이 끝났을 때 아직 담지 않은 물건이 남아 있을 수도 있는지 떠올려 볼 수 있을까요?",
            "lo와 hi가 같을 때 마지막 물건이 빠진다는 점을 제대로 짚었네요.": "10번째 줄 while lo < hi:는 lo와 hi가 같은 순간, 즉 아직 상자에 들어가지 않은 물건이 하나 남은 순간에 반복을 멈춥니다. "
                                                         "그렇다면 이 줄이 \"남은 물건이 있는 동안 계속 돈다\"는 뜻이 되려면 두 위치의 관계를 어떻게 적어야 할까요?",
        }
        for echo, rest in asks.items():
            want = rest.split(", ", 1)[1] if rest.startswith("그 말이") else rest  # 지운 문장에 기대는 첫머리는 첫 쉼표까지 뗀다
            self.assertEqual(repair(f"{echo} {rest}", fakes.PROBLEM, "정렬 안 하고 그냥 가장 큰 거랑 작은 거 찾으면 안 돼요?"), want)
        self.assertEqual(repair("그렇다고 했어요. 그 말은 맞을까요?", fakes.PROBLEM), "그 말은 맞을까요?")  # 쉼표가 없으면 그대로

    def test_cut_quote_keeps_its_marks(self):
        from ..common.talk_rules import repair

        problem = "새 기록이 그때까지 들어온 모든 기록(새 기록 포함) 가운데 점수가 높은 순서로 k등 안(1위부터 k위까지)이면 알림을 보냅니다."
        text = "문제 글의 '그때까지 들어온 모든 기록(새 기록 포함) 가운데 ... (1위부터 k위까지)이면' 문장을 다시 보면 무엇을 남겨 둬야 할까요?"
        self.assertEqual(repair(text, problem), text)
        self.assertNotIn("문제 글에 없는 인용", reply_problems(text, move="open", problem=problem))
        self.assertEqual(repair("'그때까지 ... 없는 말'을 보면 무엇을 남길까요?", problem), "그때까지 ... 없는 말을 보면 무엇을 남길까요?")

    def test_silent_e_has_batchim(self):
        from ..common.talk_rules import rename_note
        from ..debug.rules import batchim

        self.assertEqual([batchim(w) for w in ("name", "line", "table", "value", "tom", "remaining", "r", "for")], [True, True, True, False, True, True, True, False])
        # 코드 이름 뒤에 조사를 붙이지 않는다
        self.assertEqual(rename_note([["g", "name"]]), "이 블록에서 쓴 이름(`g`)을 튜터의 코드는 다른 이름(`name`)으로 불러요. 뒤 블록을 '이 블록 채우기'로 채우면 내 이름으로 바꿔 채워요.")
        self.assertEqual(rename_note([["cnt", "count"], ["r", "name"]]),
                         "이 블록에서 쓴 이름(`cnt`, `r`)을 튜터의 코드는 차례대로 다른 이름(`count`, `name`)으로 불러요. 뒤 블록을 '이 블록 채우기'로 채우면 내 이름으로 바꿔 채워요.")


class EchoClauseTest(unittest.TestCase):
    def test_qa_echo_clauses_and_praise(self):
        """평가에서 걸린 되받기 절·칭찬. 근거 질문은 사용자 말을 인용하는 것이 설계라 그대로 둔다."""
        from ..common.talk_rules import repair

        cases = {
            '방금 "모르겠어요"라고 하셨는데, 벨트 위 무게는 언제 줄어들까요?': "벨트 위 무게는 언제 줄어들까요?",
            '앞에서 두 번 "모르겠어요"라고 하셨으니, 상자가 [8, 4]일 때 0초에는 무엇이 오를까요?': "상자가 [8, 4]일 때 0초에는 무엇이 오를까요?",
            "방금 답 코드를 달라고 했으니, 그 부탁에는 답하지 않고 지금 블록만 봅니다. 벨트에 오른 상자는 언제 내릴까요?": "벨트에 오른 상자는 언제 내릴까요?",
        }
        for text, ask in cases.items():
            self.assertEqual(repair(text, fakes.PROBLEM, "모르겠어요"), ask)
        self.assertEqual(repair('방금 "모르겠어요"라고 하셨는데, 천천히 봐요.', fakes.PROBLEM), '방금 "모르겠어요"라고 하셨는데, 천천히 봐요.')  # 남는 질문이 없다
        leaked = '"답을 달라"고 했으니 안내 문장은 앞에 따로 붙고, 저는 지금 블록을 겨눈 질문 한 문장만 씁니다. 2초에 내릴 상자는 무엇인가요?'  # 실제 모델 확인
        self.assertEqual(repair(leaked, fakes.PROBLEM), "2초에 내릴 상자는 무엇인가요?")
        leaked = "이 답 코드를 달라고 하셨지만, 그 부탁에는 답하지 않고 지금 블록을 겨눠 볼게요. 작은 예로 [8, 4]를 봐요. 어느 쪽이 먼저 내릴까요?"
        self.assertEqual(repair(leaked, fakes.PROBLEM), "작은 예로 [8, 4]를 봐요. 어느 쪽이 먼저 내릴까요?")
        self.assertEqual(repair("그러면 문제 글에서 0초에 무엇이 오를까요?", fakes.PROBLEM), "문제 글에서 0초에 무엇이 오를까요?")
        said = "왼쪽 끝 left는 0, 오른쪽 끝 right는 마지막 자리로 두고 반으로 나눠요"
        basis = "'왼쪽 끝 left는 0, 오른쪽 끝 right는 마지막 자리로 두고'라고 하셨는데, 이 생각은 문제 글에 나온 것인가요, 아니면 짐작인가요?"
        self.assertEqual(repair(basis, fakes.PROBLEM, said, "basis"), basis)
        for text in ("좋은 관찰이에요. 3+8은 몇일까요?", "잘 짚었어요. 그다음은?", "정확히 보셨어요. 다음은요?"):
            self.assertIn("동의로 시작", reply_problems(text, move="open", problem=""), text)

    def test_debug_reply_is_checked_for_praise(self):
        from ..debug import nodes
        from ..state import TutorRequest

        draft = {"step_name": "trace", "recent": [], "hash": "h", "kind": "logic", "line": 7, "cause": "", "fixed_line": "", "step": 1}
        state = {"request": TutorRequest(kind="debug", problem_id="p1", code="a = 1", text="모르겠어요"), "ctx": fakes.context(),
                 "draft": draft, "reply_draft": "좋은 관찰이에요. 3+8이 11이 되는 줄은 어디일까요?"}
        self.assertEqual(nodes.check_reply(state)["result"]["reply"], nodes.rules.FALLBACK["trace"])


class ToldAnswerTest(unittest.TestCase):
    def test_statement_of_block_answer_is_dropped(self):
        """의자·가이드가 블록의 답(시작 값, 빈칸의 식)을 평서문으로 말했다. 그 문장을 지우고 질문만 남긴다."""
        from ..common.talk_rules import repair

        problem = "0초에 맨 앞 상자가 벨트에 오릅니다. 벨트 위에 있는 상자들의 무게 합은 언제나 limit 이하여야 합니다."
        start = "    load = 0        # 벨트 위 무게 합\n    time = 0\n    next_box = 0    # 줄의 맨 앞 상자 번호"
        told = {
            "시작하기 전에 세 가지를 기억해 둬야 해요. 벨트 위 무게 합은 0, 현재 시각은 0, 맨 앞 상자 번호는 0이에요. 0초에는 무엇이 오를까요?":
                "시작하기 전에 세 가지를 기억해 둬야 해요. 0초에는 무엇이 오를까요?",
            "load는 0, time은 0으로 두면 돼요. 그다음에는 무엇을 볼까요?": "그다음에는 무엇을 볼까요?",
        }
        for text, left in told.items():
            self.assertIn("답을 말함", reply_problems(text, move="open", problem=problem, reference=start))
            self.assertEqual(repair(text, problem, reference=start), left)
        self.assertEqual(repair("빈칸에는 time을 1 올리는 식이 들어가요. 어떻게 쓸까요?", problem, reference="        time += 1"), "어떻게 쓸까요?")
        walk = "        if heights[i] > heights[i - 1]:\n            length += 1\n        else:\n            length = 1"
        self.assertEqual(repair("높으면 length를 늘리고, 아니면 length를 1로 되돌려야 합니다. 그 길이는 어디에 쓰일까요?", problem, reference=walk),
                         "그 길이는 어디에 쓰일까요?")
        for fine in ("벨트 위 무게 합은 0에서 시작해야 할까요?",  # 질문
                     "'0초에 맨 앞 상자가 벨트에 오릅니다.'라고 적혀 있어요. 그럼 처음에 무엇을 정해 둘까요?",  # 문제 글 인용
                     "limit이 10이고 boxes가 [4, 4, 4]라고 해 봅시다. 셋째 상자는 언제 오를까요?"):  # 작은 예
            self.assertNotIn("답을 말함", reply_problems(fine, move="trace", problem=problem, reference=start), fine)
        self.assertIn("답을 말함", reply_problems("벨트 위 무게 합과 맨 앞 상자 번호는 0이에요.", move="open", problem=problem, reference=start))  # 지울 수 없으면 대체 질문


class DebugSaidLineTest(unittest.TestCase):
    def test_line_named_in_reply_is_marked(self):
        """말로 '7번째 줄'을 짚었는데 결과의 line이 비어 편집기에 표시가 없었다."""
        from ..debug import nodes
        from ..state import TutorRequest

        code = "\n".join(f"x{n} = {n}" for n in range(1, 9))
        draft = {"step_name": "trace", "recent": [], "hash": "h", "kind": "logic", "line": 0, "cause": "", "fixed_line": "", "step": 1}

        def line_of(reply):
            state = {"request": TutorRequest(kind="debug", problem_id="p1", code=code, text="모르겠어요"), "ctx": fakes.context(),
                     "draft": dict(draft), "reply_draft": reply}
            return nodes.check_reply(state)["result"]["line"]

        self.assertEqual(line_of("7번째 줄의 조건식을 계산할 때 3+8은 몇이 되나요?"), 7)
        self.assertIsNone(line_of("3번째 줄과 7번째 줄을 견주면 무엇이 다를까요?"))  # 여러 줄
        self.assertIsNone(line_of("12번째 줄에서 값은 어떻게 되나요?"))  # 코드 줄 수 밖


class DebugReportedLineTest(unittest.TestCase):
    def test_error_line_from_grader_beats_model_guess(self):
        """오류가 난 줄은 채점 결과가 안다(컴파일 오류의 줄, 실패한 케이스의 줄). 모델이 짐작한 줄보다 먼저다. 틀린 답(오류 없음)은 모델의 줄을 쓴다."""
        from ..debug import nodes, rules

        self.assertEqual(rules.error_line({"compile_line": 5, "cases": []}), 5)
        self.assertEqual(rules.error_line({"cases": [{"status": "runtime_error", "line": 4, "error": "boom"}]}), 4)
        self.assertEqual(rules.error_line({"cases": [{"status": "runtime_error", "error": 'File "solution.py", line 3\nNameError: x'}]}), 3)  # 채점기가 줄을 못 주면 오류 글
        self.assertIsNone(rules.error_line({"cases": [{"status": "failed", "got": "1"}]}))

        def located(report, model_line):
            from unittest import mock

            from ..state import Diagnosis, TutorRequest

            code = "\n".join(f"x{n} = {n}" for n in range(1, 9))
            with mock.patch.object(nodes, "llm") as llm:
                llm.return_value.use.return_value = Diagnosis(kind="logic", line=model_line, cause="c", fixed_line="", pitfall="")
                state = {"request": TutorRequest(kind="debug", problem_id="p1", code=code, report=report), "ctx": fakes.context(),
                         "draft": {"candidates": [], "hash": "h", "cached": False, "previous": None}}
                return nodes.locate(state)["draft"]["line"]

        self.assertEqual(located({"status": "runtime_error", "cases": [{"status": "runtime_error", "line": 6, "error": "boom"}]}, 2), 6)
        self.assertEqual(located({"status": "failed", "cases": [{"status": "failed", "got": "1"}]}, 2), 2)


class SymptomParticleTest(unittest.TestCase):
    def test_particle_follows_last_sound(self):
        """디버그 첫 말이 '9이(가) 나왔어요'였다. 받침에 맞는 조사를 고른다."""
        from ..debug.rules import symptom

        def said(got):
            return symptom({"status": "failed", "cases": [{"input": "[3]", "expected": "4", "got": got, "status": "failed"}]})

        self.assertTrue(said("9").endswith("4인데 9가 나왔어요."))
        self.assertTrue(said("10").endswith("10이 나왔어요."))
        self.assertTrue(said('"tom"').endswith('"tom"이 나왔어요.'))
        self.assertTrue(said("[1, 2]").endswith("[1, 2]가 나왔어요."))
        self.assertTrue(said("사과").endswith("사과가 나왔어요."))
        self.assertTrue(said("").endswith("4인데 아무것도 나오지 않았어요."))


class GrammarRuleTest(unittest.TestCase):
    """이름 바꾸기·실행 없는 통과·진입 함수 머리는 언어의 문법으로만 가른다(기본 문제에 없는 꼴의 입력)."""

    def test_type_names_in_typed_declarations_are_not_written_names(self):
        """형을 적은 선언의 형 이름(Int, i32, int)을 쓴 이름으로 읽어 '그 이름으로 맞춰 주세요'에 형 이름이 섞였다."""
        from ..turn.pairs import writes
        self.assertEqual(writes("var answer: Int = 0\nvar at: Int = 1", "kotlin"), ["answer", "at"])
        self.assertEqual(writes("let mut best: i32 = -1;\nlet n: usize = v.len();", "rust"), ["best", "n"])
        self.assertEqual(writes("var count int = 0\ncount = 3", "go"), ["count"])
        self.assertEqual(writes("int total = 0;\ntotal += 2;", "java"), ["total"])  # 형이 앞에 오는 언어는 그대로
        # 선언 이름 뒤부터 '=' 앞까지는 모두 형이다(형 꼴을 하나씩 늘리지 않는다)
        self.assertEqual(writes('let label: &str = "x";', "rust"), ["label"])
        self.assertEqual(writes("var cells [3]int = [3]int{}\nvar head *Item = nil\nvar seen map[string]int = map[string]int{}", "go"), ["cells", "head", "seen"])
        self.assertEqual(writes("const limit int = 3", "go"), ["limit"])
        self.assertEqual(writes("var lo, hi int = 0, 9", "go"), ["lo", "hi"])

    def test_swap_names_changes_only_name_positions(self):
        from ..common.solution import swap_names

        rows = [  # (언어, 계획 코드, 이름 표, 바뀐 코드)
            ("python", 'print(answer, end=" ")', {"end": "right"}, 'print(answer, end=" ")'),  # 키워드 인자 이름은 이름이 아니다
            ("python", "items.sort(key=lambda p: p[1])\nkey = 3", {"key": "k"}, "items.sort(key=lambda p: p[1])\nk = 3"),
            ("python", "q = deque(maxlen=k)\nm = max(xs, default=start)", {"maxlen": "m2", "k": "w", "default": "d", "start": "s"},
             "q = deque(maxlen=w)\nm = max(xs, default=s)"),
            ("python", "def helper(n, seen=None):\n    return seen", {"seen": "visited"}, "def helper(n, visited=None):\n    return visited"),  # def 머리의 기본값은 매개변수다
            ("python", 'print(f"Case #{t}: {answer}", "answer")', {"t": "case", "answer": "best"}, 'print(f"Case #{case}: {best}", "answer")'),
            ("python", 'a = f"{count=}" + f"{count:>{width}}" + f"{{count}}" + "{count}"', {"count": "c", "width": "w"},
             'a = f"{count=}" + f"{c:>{w}}" + f"{{count}}" + "{count}"'),  # '{x=}'는 식의 글자가 출력된다
            ("python", 's = """count"""\nt = count  # don\'t keep count', {"count": "c"}, 's = """count"""\nt = c  # don\'t keep c'),  # 주석은 돌지 않는다: 낱말을 맞춘다
            ("kotlin", 'println("count=$count ${count + 1}")\nval p = Pair(first = a, second = first)', {"count": "c", "first": "f"},
             'println("count=$c ${c + 1}")\nval p = Pair(first = a, second = f)'),
            ("javascript", 'console.log(`count: ${count}`, "count", count)', {"count": "c"}, 'console.log(`count: ${c}`, "count", c)'),
            ("rust", "fn longest<'a>(x: &'a str, y: &'a str) -> &'a str { if x.len() > y.len() { x } else { y } }", {"x": "first", "y": "second"},
             "fn longest<'a>(first: &'a str, second: &'a str) -> &'a str { if first.len() > second.len() { first } else { second } }"),  # 수명 표기는 문자열이 아니다
            ("rust", "let c = 'x'; let q = '\\''; let n = x + 1;", {"x": "z"}, "let c = 'x'; let q = '\\''; let n = z + 1;"),
            ("go", 'm[x] = len("x") + x', {"x": "key"}, 'm[key] = len("x") + key'),
            ("cpp", "char q = '\"'; int z = count; // count's", {"count": "c"}, "char q = '\"'; int z = c; // c's"),
            ("java", 'f(x = 5); String s = "x";', {"x": "y"}, 'f(y = 5); String s = "x";'),  # Java의 괄호 안 '='는 대입이다
            ("cpp", "node->x = x;", {"x": "y"}, "node->x = y;"),  # '->' 뒤는 멤버다
            ("cpp", "int c = std::count(v.begin(), v.end(), 1) + count;", {"count": "cnt"}, "int c = std::count(v.begin(), v.end(), 1) + cnt;"),  # '::' 뒤는 경로다
            ("rust", "let m = i32::max(x, 1) + Vec::count(&v);", {"x": "y", "count": "cnt"}, "let m = i32::max(y, 1) + Vec::count(&v);"),
            ("kotlin", "val g = xs.map(Foo::x) + x", {"x": "y"}, "val g = xs.map(Foo::x) + y"),
            ("python", "r = a[::x] + a[x::2]", {"x": "y"}, "r = a[::y] + a[y::2]"),  # Python의 '::'는 조각의 간격이다(변수가 온다)
            ("java", "list.forEach(x->use(x));", {"x": "y"}, "list.forEach(y->use(y));"),  # Java의 '->'는 람다다
        ]
        for language, code, names, want in rows:
            with self.subTest(language=language, code=code):
                self.assertEqual(swap_names(code, names, language), want)

    def test_swap_names_known_limits_are_written_down(self):
        """어휘를 정규식으로 읽는 한계: 이런 꼴은 드물어 규칙을 더하지 않는다. 잘못 바뀐 코드는 이어 돌린 실행이 실패해 드러난다(틀린 통과로 가지 않는다).
        아래는 지금의 동작이다. 알려진 한계가 바뀌면 이 시험이 알려 준다."""
        from ..common.solution import swap_names

        rows = [
            ("javascript", "const r = /x/g;", {"x": "Y"}, "const r = /Y/g;"),  # 정규식 글자
            ("javascript", "const a = `x ${x} ${`in ${count} x`} x`;", {"x": "Y", "count": "cnt"}, "const a = `x ${Y} ${`in ${cnt} Y`} x`;"),  # 겹친 백틱
            ("kotlin", 'val a = "${f("x")} $x"\nval b = "${ if (x > 0) "x" else "y" }"', {"x": "Y"},
             'val a = "${f("Y")} $Y"\nval b = "${ if (x > 0) "Y" else "y" }"'),  # ${} 안의 문자열
            ("rust", 'let a = r#"x "quoted" x"#;', {"x": "Y"}, 'let a = r#"x "quoted" Y"#;'),  # r#"…"#
            ("cpp", 'auto s = R"d(x)d";', {"x": "Y"}, 'auto s = R"d(Y)d";'),  # 구분자 있는 원시 문자열
            ("java", 'String t = """\n  \\"""x\\"""\n""";', {"x": "Y"}, 'String t = """\n  \\"""Y\\"""\n""";'),  # 텍스트 블록 안의 이스케이프
            ("python", 'a = f"{d["x"]}"\nb = f"{x:{"x"}}"', {"x": "Y"}, 'a = f"{d["Y"]}"\nb = f"{x:{"Y"}}"'),  # 3.12의 같은 따옴표 중첩
            ("cpp", "#include <x>\n", {"x": "Y"}, "#include <Y>\n"),
            ("rust", "'x: loop { break 'x; }", {"x": "Y"}, "'Y: loop { break 'Y; }"),  # 라벨
            ("python", "def h(x):\n    return x\ny = h(x=x)", {"x": "Y"}, "def h(Y):\n    return Y\ny = h(x=Y)"),  # 머리의 매개변수와 호출의 키워드 인자가 짝이 안 맞는다
            ("kotlin", "fun h(x: Int) = x\nval y = h(x = x)", {"x": "Y"}, "fun h(Y: Int) = Y\nval y = h(x = Y)"),
            ("python", "sorted(a, key=lambda x=1: x)", {"x": "Y"}, "sorted(a, key=lambda x=1: Y)"),  # 람다의 기본값
        ]
        for language, code, names, want in rows:
            with self.subTest(language=language, code=code):
                self.assertEqual(swap_names(code, names, language), want)

    def test_only_same_text_passes_without_run(self):
        """실행 없이 통과하는 길은 줄 끝 공백·빈 줄만 다를 때다. 주석·공백·틀 줄을 떼고 견주면 같아지던 다른 코드는 실행으로 간다."""
        from ..turn.code_check import _rows

        differ = [  # (계획, 내 코드)
            ("    for (int x : v) {\n        total += x;\n    }", "    for (int x : v) {\n        total += x;\n    }\n}"),  # 함수를 닫는 '}'가 하나 더
            ('const dirs = [\n    "up",\n    "down"\n];', 'const dirs = [\n    "up",\n    "dwn"\n];'),  # 문자열만 있는 줄
            ("fmt.Println(\n\tanswer,\n)", "fmt.Println(\n\tanswer,"),  # 닫는 ')' 줄을 빠뜨림
            ('print(f"Case #{t}: {answer}")', 'print(f"Case #{t} - {answer * 2}")'),  # 문자열 안의 '#'
            ('print(" ".join(row))', 'print("  ".join(row))'),  # 문자열 안의 공백
            ("from collections import deque\nq = deque()", "q = deque()"),  # 가운데의 import
        ]
        for plan, mine in differ:
            self.assertNotEqual(_rows(mine), _rows(plan), mine)
        self.assertEqual(_rows("x = 1   \n\n\ny = 2\n"), _rows("x = 1\ny = 2"))

    def test_entry_params_follow_each_grammar(self):
        from ..common.solution import entry_params

        rows = [("python", "def solution(loans, k):"), ("kotlin", "fun solution(loans: Array<String>, k: Int): Array<String> {"),
                ("rust", "pub fn solution(mut loans: Vec<String>, k: i32) -> Vec<String> {"), ("go", "func solution(loans []string, k int) []string {"),
                ("cpp", "vector<string> solution(vector<string> loans, int k) {"), ("java", "    public String[] solution(String[] loans, int k) {"),
                ("javascript", "function solution(loans, k) {")]
        for language, head in rows:
            self.assertEqual(entry_params(head + "\n", language), ["loans", "k"], language)
        self.assertIsNone(entry_params("const solution = (loans, k) => {", "javascript"))  # 알아보지 못한 머리는 같다고 하지 않는다

    def test_entry_params_read_the_last_word_of_a_declaration(self):
        """C 계열(C·C++·Java)·Go의 선언에서 이름은 타입 다음의 마지막 낱말이다. '::'는 경로라 'name: Type'의 ':'가 아니고, 꺾쇠·괄호 안의 쉼표에서 끊지 않으며,
        머리가 여러 줄이어도 괄호가 닫힐 때까지 읽는다. 닫히지 않으면 알아보지 못한 것이다."""
        from ..common.solution import entry_params

        rows = [("cpp", "int solution(std::vector<int>& nums, int k) {", ["nums", "k"]),
                ("cpp", "long long solution(std::string s, std::unordered_map<int,int> m) {", ["s", "m"]),
                ("cpp", "int solution(const string &s, int *p, map<int, int> m) {", ["s", "p", "m"]),
                ("cpp", "vector<int> solution(vector<vector<int>>& grid,\n                     int k,\n                     map<int, pair<int, int>> m) {", ["grid", "k", "m"]),
                ("cpp", "int solution(int a, std::vector<std::pair<int,int>>& v) {", ["a", "v"]),
                ("java", "public int[] solution(int[] arr, java.util.List<String> names, final int k) {", ["arr", "names", "k"]),
                ("go", "func solution(a, b int, names []string) int {", ["a", "b", "names"]),
                ("go", "func solution(a, b int,\n\tnames []string) int {", ["a", "b", "names"]),
                ("kotlin", "fun solution(m: Map<Int, Int>, f: kotlin.collections.List<Int>): Int {", ["m", "f"]),
                ("rust", "fn solution(m: std::collections::HashMap<i32, i32>, mut v: Vec<i32>) -> i32 {", ["m", "v"]),
                ("python", "def solution(nums,\n             k):", ["nums", "k"]),
                ("python", "def solution(nums,\n", None), ("kotlin", "fun solution(a: Int,", None)]
        for language, head, want in rows:
            with self.subTest(language=language, head=head):
                self.assertEqual(entry_params(head + "\n", language), want)

    def test_every_builtin_starter_and_solution_share_a_head(self):
        """기본 문제 모든 언어의 시작 코드와 정답 풀이는 진입 함수 머리(인자 이름·차례)가 같다: 사용자가 시작 코드대로 쓴 블록이 풀이 코드와 이어진다."""
        import json
        from pathlib import Path

        from ..common.solution import entry_params

        rows = json.loads((Path(__file__).resolve().parents[2] / "ui" / "builtin.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(rows), 75)
        for row in rows:
            for language in row["languages"]:
                with self.subTest(problem=row["id"], language=language):
                    start = entry_params(row["starters"][language], language)
                    self.assertIsNotNone(start)
                    self.assertEqual(entry_params(row["solutions"][language], language), start)


class PlainWordsTest(unittest.TestCase):
    """모델에 넘기는 말과 화면에 나가는 고정 말에 내부 말·영어 꼬리표·다른 곳의 문제 이름이 없다."""

    def test_outside_problem_rule_reaches_every_prompt_that_speaks(self):
        from ..common.scope import OUTSIDE_PROBLEMS, PRINCIPLES
        from ..debug.prompts import SPEAK_SYSTEM
        from ..feedback.prompts import analyze_messages
        from ..plan.prompts import HINT_RULES, SOLVE_SYSTEM

        for text in (PRINCIPLES, SPEAK_SYSTEM, "\n".join(HINT_RULES), SOLVE_SYSTEM):
            self.assertIn(OUTSIDE_PROBLEMS, text)
        state = fakes.make_state("feedback", fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1))
        self.assertIn(OUTSIDE_PROBLEMS, analyze_messages(state)[1]["content"])  # similar_hint 줄
        self.assertNotIn("사용자에게 보이지 않고", SOLVE_SYSTEM)  # 풀이 방향·단서·단계는 해설에 실린다

    def test_english_labels_become_words(self):
        from ..common.talk_rules import kind_word
        from ..debug.prompts import _result_lines

        self.assertEqual((kind_word("var_during"), kind_word("branch")), ("풀이 중에 만드는 변수", "경우 나누기"))
        self.assertEqual(kind_word("new_kind"), "new_kind")  # 모르는 종류는 그대로 둔다
        state = fakes.make_state("debug", fakes.context(), code="x = 1", report={"status": "runtime_error", "cases": []})
        self.assertIn("채점 결과:실행 오류", "\n".join(_result_lines(state)))

    def test_debug_fallback_reads_whole_without_a_line_number(self):
        from ..debug.rules import FALLBACK, fallback

        for name in FALLBACK:
            said = fallback(name, None)
            self.assertNotIn("{line}", said)
            self.assertNotIn("번째", said)
            self.assertIn("의심되는 줄" if "{line}" in FALLBACK[name] else FALLBACK[name][:6], said)
        self.assertIn("3번째 줄", fallback("cause", 3))
