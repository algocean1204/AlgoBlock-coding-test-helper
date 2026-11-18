"""튜터 서비스 끝까지(SQLite 파일 + 가짜 모델). A2 불러오기와 A12 저장이 진짜로 돈다."""

import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from . import fakes
from ..llm import FakeLlm, LlmTimeout
from ..common.talk_rules import CHECKED, FALLBACK
from ..main import Tutor
from ..turn.moves import HINTS_DONE_UNFOUND, WRITE_TIP
from ..store.codec import plan_to_json
from ..store.schema import SCHEMA

DRAFT = {"plan.draft_blocks": [fakes.drafted([fakes.as_dict(b) for b in fakes.hinted()])]}
# 풀이 가이드와, 그 코드의 줄 구간으로 나눈 블록 초안
CODE = "def solution(a, b):\n    count = {}\n    for name in a:\n        count[name] = count.get(name, 0) + 1"
SOLVED = {"clues": ["'제목이 같으면 같은 책입니다' → 제목마다 횟수를 세야 한다"],
          "approach": "이름마다 몇 번 나왔는지 세어 두고 둘째 명단의 이름을 하나씩 뺀다.", "steps": ["이름을 센다 — 같은 이름이 있어서", "둘째 명단을 뺀다 — 남는 하나를 찾으려고"], "code": CODE}
LINED = {"plan.draft_blocks": [fakes.drafted([{**fakes.as_dict(b), "reference": "", "lines": span} for b, span in zip(fakes.hinted(), ([1, 2], [3, 4]))])]}


class TutorTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.dir.name) / "tutor.db")

    def tearDown(self):
        self.dir.cleanup()

    def tutor(self, scripts):
        fake = FakeLlm(scripts)
        tutor = Tutor(self.path, client=fake)
        tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
        if "plan.abstract" not in scripts:
            tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])  # 뼈대가 있으면 다시 뽑지 않는다
        return tutor, fake

    def test_chair_conversation_is_saved_with_moves(self):
        draft = {"plan.draft_blocks": [fakes.drafted([fakes.as_dict(b) for b in fakes.thinking()])]}
        tutor, fake = self.tutor({**draft, "chair.judge": ["[check]Y g", "[check]Y t"], "chair.ask": ["'이름을 센다'는 생각의 근거는 문제 글에 있나요, 짐작인가요?"],
                                    "chair.check_code": ["[check]Y"]})
        try:
            start = tutor.turn("p1", "chair", "start")
            self.assertEqual(start.status, 200)
            self.assertEqual(start.body["messages"][0]["text"], fakes.HINTS1[0])
            self.assertEqual(set(start.body["blocks"][0]), {"id", "kind", "name"})
            self.assertTrue(all(b["name"] is None for b in start.body["blocks"]))  # 의자: 지금 블록 이름도 사용자가 찾을 답이라 가린다
            self.assertEqual(start.body["blocks"][0]["kind"], "condition")  # 종류는 보여 준다
            self.assertIsNotNone(tutor.session("p1").body["blocks"][0]["name"])  # 가이드·기본 보기는 지금 블록까지
            basis = tutor.turn("p1", "chair", "message", text="이름을 세면 돼요")
            self.assertEqual((basis.body["open_count"], len(basis.body["messages"])), (1, 3))
            wrote = tutor.turn("p1", "chair", "message", text="문제에 제목이 같으면 같은 책이라고 해서요")
            # 말로 찾았다: 넘기지 않고 그 블록의 코드로 적으라는 고정 말. 지금 블록의 이름은 열린다(그 칸에 코드를 적는다)
            self.assertEqual((wrote.body["open_count"], wrote.body["messages"][-1]["text"], wrote.body["messages"][-1]["move"]), (1, WRITE_TIP, "write"))
            self.assertEqual([b["name"] for b in wrote.body["blocks"]], ["입력받기", None])
            self.assertEqual([b["name"] for b in tutor.session("p1", "chair").body["blocks"]], ["입력받기", None])
            moved = tutor.turn("p1", "chair", "block_filled", block_id="b1", code="count = {}")  # 그 블록의 코드 확인이 통과해야 다음 블록이 열린다
            self.assertEqual(moved.body["open_count"], 2)
            self.assertEqual([b["name"] for b in moved.body["blocks"]], ["입력받기", None])  # 다음 블록 이름은 가린다
            self.assertTrue(moved.body["messages"][-1]["text"].endswith("다음은 '반복' 블록이에요. " + fakes.HINTS2[0]))  # 채점 함수가 없어 읽고 본 판단이라는 말이 앞에 붙는다
            self.assertEqual([m["block_index"] for m in moved.body["messages"]], [0, 0, 0, 0, 0, 0, 1])  # 화면 구분선은 그 말의 블록 종류
            rows = tutor.store.conn.execute("SELECT role, block_index, move FROM message WHERE problem_id='p1' ORDER BY id").fetchall()
            self.assertEqual([tuple(r) for r in rows], [("service", 0, "open"), ("user", 0, None), ("service", 0, "basis"),
                                                        ("user", 0, None), ("service", 0, "write"), ("user", 0, CHECKED + "?"), ("service", 1, "open")])
            raw = tutor.store.conn.execute("SELECT plan_json FROM tutor_session WHERE problem_id='p1'").fetchone()[0]
            self.assertIn('"algorithm": "hash"', raw)
            self.assertNotIn("reference", json.dumps(moved.body))
            self.assertNotIn("REF_ONE", json.dumps(tutor.session("p1").body))
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks", "chair.judge", "chair.ask", "chair.check_code"])  # 근거 질문의 평서 답은 판정 0회
        finally:
            tutor.close()

    def test_explain_and_feedback_are_reused(self):
        analysis = {"analysis": "같은 이름이 둘이면요? [확실] 실패다.", "similar_hint": "센다", "advice": "정석 순서로"}
        tutor, fake = self.tutor({**DRAFT, "explain.write": [{"sections": fakes.SECTIONS}], "feedback.assess": ["[check]30 Y"], "feedback.analyze": [analysis]})
        try:
            first = tutor.explain("p1")
            self.assertEqual(first.body["explain"]["sections"][0]["title"], "문제에서 읽을 것")
            calls = len(fake.calls)
            self.assertEqual(tutor.explain("p1").body, first.body)
            self.assertEqual(len(fake.calls), calls)  # 저장된 해설, 모델 0회

            self.assertEqual(tutor.feedback("p1").body["detail"]["code"], "not_submitted")
            tutor.store.add_submission("p1", "set(a) - set(b)", False)
            fed = tutor.feedback("p1")
            self.assertEqual((fed.status, fed.body["strategy"], fed.body["similar_hint"]), (200, "canonical", "해시: 센다"))
            self.assertNotIn("score", fed.body)
            calls = len(fake.calls)
            self.assertEqual(tutor.feedback("p1").body, fed.body)
            self.assertEqual(len(fake.calls), calls)  # 같은 제출, 모델 0회
            self.assertEqual(tutor.feedback_get("p1").body, fed.body)
        finally:
            tutor.close()

    def test_errors_save_nothing(self):
        tutor, _ = self.tutor({**DRAFT, "chair.ask": [LlmTimeout("늦음")], "chair.judge": ["[check]N1"]})
        try:
            self.assertEqual(tutor.turn("p9", "chair", "start").status, 404)
            self.assertEqual(tutor.turn("p1", "chair", "start").status, 200)
            before = tutor.store.message_count("p1")
            failed = tutor.turn("p1", "chair", "message", text="한 번씩만 세면 될 것 같아요")
            self.assertEqual((failed.status, failed.body["detail"]["code"]), (504, "llm_timeout"))
            self.assertEqual(tutor.store.message_count("p1"), before)
            self.assertEqual(tutor.turn("p1", "chair", "message", text="  ").status, 400)
            self.assertEqual(tutor.store.message_count("p1"), before)
        finally:
            tutor.close()

    def test_store_failures(self):
        tutor, fake = self.tutor({**DRAFT})
        try:
            with mock.patch.object(tutor.store, "load", side_effect=sqlite3.OperationalError("locked")):
                failed = tutor.turn("p1", "chair", "start")
            self.assertEqual((failed.status, failed.body["detail"]["code"], fake.calls), (500, "store_failed", []))
            with mock.patch.object(tutor.store, "save_success", side_effect=sqlite3.OperationalError("disk")):
                failed = tutor.turn("p1", "chair", "start")
            self.assertEqual(failed.body["detail"]["code"], "store_failed")
            self.assertEqual(tutor.store.message_count("p1"), 0)
            real_load = tutor.store.load
            calls = {"n": 0}

            def load_once(problem_id):
                calls["n"] += 1
                if calls["n"] > 1:
                    raise sqlite3.OperationalError("reread")
                return real_load(problem_id)

            fake.scripts["plan.draft_blocks"] = list(DRAFT["plan.draft_blocks"])
            with mock.patch.object(tutor.store, "load", side_effect=load_once):
                ok = tutor.turn("p1", "chair", "start")
            self.assertEqual((ok.status, ok.body["messages"][-1]["text"], ok.body["open_count"]), (200, fakes.HINTS1[0], 1))
            self.assertEqual(tutor.store.message_count("p1"), 1)
        finally:
            tutor.close()

    def test_fill_opens_next_block_then_next_event_asks_its_first_question(self):
        tutor, fake = self.tutor({**LINED, "plan.solve": [SOLVED]})  # 채우기는 풀이 가이드의 코드로 한다(가이드가 없으면 채우지 않는다)
        try:
            tutor.turn("p1", "chair", "start")
            self.assertEqual(tutor.turn("p1", "chair", "next").status, 400)  # 지금 블록에는 이미 질문이 있다
            filled = tutor.fill("p1", "b1")
            self.assertEqual(filled.body["open_count"], 2)
            opened = tutor.turn("p1", "chair", "next")
            self.assertEqual(opened.status, 200)
            self.assertEqual(opened.body["messages"][-1]["text"], "다음은 '반복' 블록이에요. " + fakes.HINTS2[0])
            self.assertEqual(fakes.tasks(fake).count("chair.ask"), 0)  # 저장 질문이라 모델 0회
            self.assertEqual(tutor.turn("p1", "chair", "next").status, 400)
        finally:
            tutor.close()

    def test_prepare_builds_plan_ahead_so_first_question_is_instant(self):
        """문항을 열 때 미리 계획까지 만들어 둔다. 그러면 시작은 저장 질문이라 모델 0회다. 그 사이 코드를 썼으면 그 코드로 다시 짠다."""
        abstract = {"spec": "문자열 배열 둘. 남는 원소 하나.", "patterns": ["dup_names"], "size": 100000, "skills": ["dict_count"]}
        tutor, fake = self.tutor({"plan.abstract": [abstract], "plan.draft_blocks": DRAFT["plan.draft_blocks"] * 3, "plan.assess": ["[check]70 Y"]})
        try:
            ready = tutor.prepare("p1")
            self.assertEqual((ready.status, ready.body["blocks"], ready.body["patterns"]), (200, 2, ["dup_names"]))
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.plan.strategy, ctx.open_count, ctx.size, ctx.skills, tutor.store.message_count("p1")), ("fresh", 1, 100000, ["dict_count"], 0))
            self.assertIn("이중 반복은 안 된다", fakes.prompt(fake, "plan.draft_blocks"))  # 입력 크기 경험칙(참고)
            self.assertIn("딕셔너리로 개수 세기", fakes.prompt(fake, "plan.draft_blocks"))  # 구현 기술(참고)
            fake.calls.clear()
            self.assertEqual(tutor.prepare("p1").status, 200)  # 이미 있으면 아무것도 안 한다
            self.assertEqual(tutor.turn("p1", "chair", "start").body["messages"][0]["text"], fakes.HINTS1[0])
            self.assertEqual(fake.calls, [])  # 첫 질문: 모델 0회
            tutor.store.put_problem("p2", "python", fakes.PROBLEM)
            tutor.store.put_fact("p2", "뼈대", [])
            tutor.prepare("p2")
            tutor.store.update_code("p2", "def solution(a, b):\n    return a[0]")  # 계획을 만든 뒤 코드를 먼저 썼다
            fake.calls.clear()
            tutor.turn("p2", "chair", "start")
            self.assertEqual(fakes.tasks(fake), ["plan.assess", "plan.solve", "plan.draft_blocks"])  # 그 코드를 채점해 다시 짠다
            self.assertEqual(tutor.store.load("p2").plan.strategy, "keep_flow")
        finally:
            tutor.close()

    def test_feedback_does_not_replan_and_costs_two_calls(self):
        """혼자 푼 사람은 계획을 만든 뒤 코드를 먼저 쓴 것과 같다. 피드백은 제출 코드를 자기 채점으로 보므로 계획을 다시 짜지 않는다: 모델 둘(채점, 분석)."""
        analysis = {"analysis": "같은 이름이 둘이면요? [확실] 실패다.", "similar_hint": "센다", "advice": "정석 순서로"}
        tutor, fake = self.tutor({**DRAFT, "feedback.assess": ["[check]30 Y"], "feedback.analyze": [analysis]})
        try:
            tutor.prepare("p1")
            tutor.store.update_code("p1", "def solution(a, b):\n    return a[0]")  # 계획을 만든 뒤 코드를 먼저 썼다(블록은 쓰지 않았다)
            tutor.store.add_submission("p1", "def solution(a, b):\n    return a[0]", False)
            fake.calls.clear()
            fed = tutor.feedback("p1")
            self.assertEqual((fed.status, fakes.tasks(fake)), (200, ["feedback.assess", "feedback.analyze"]))
            self.assertEqual(tutor.store.load("p1").plan.strategy, "fresh")  # 계획은 그대로다
            prompt = fakes.prompt(fake, "feedback.analyze")
            self.assertNotIn("블록(정석 흐름 순서)", prompt)  # 블록을 쓰지 않은 풀이에는 블록 자료를 넘기지 않는다
            self.assertIn("블록 방식을 쓰지 않고 혼자 풀었다", prompt)
        finally:
            tutor.close()

    def test_plan_uses_ontology_and_user_history_but_not_past_solutions(self):
        """블록의 신호·힌트에는 온톨로지 1-hop(기법·함정)과 이 사용자가 되풀이한 실수가 참고로 들어간다.
        지난 문항은 풀이를 정하지 않는다: 풀이 가이드와 블록 프롬프트에 넣지 않고, 풀어 본 문항이 같은 구조라고 판정되면 한 줄(link)만 남긴다."""
        abstract = {"spec": "문자열 배열 둘. 한쪽에만 남는 원소 하나. 같은 값 중복 가능.", "patterns": ["dup_names", "없는_패턴"]}
        tutor, fake = self.tutor({"plan.abstract": [abstract, abstract], "plan.draft_blocks": LINED["plan.draft_blocks"] * 4,
                                  "plan.solve": [SOLVED] * 4, "plan.gate": ["Y", "N"], "debug.locate": [self.FOUND],
                                  "chair.ask": ["무엇을 기록해 둬야 할까요?"] * 3})  # 다른 문제 글에서는 저장 질문의 인용이 맞지 않아 첫 질문을 새로 만든다
        try:
            tutor.turn("p1", "chair", "start")
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.spec, ctx.patterns), (abstract["spec"], ["dup_names"]))  # 온톨로지에 없는 id는 버린다
            first = fakes.prompt(fake, "plan.draft_blocks")
            self.assertIn("개수 세기(딕셔너리)", first)
            self.assertIn("있다·없다만으로는 여러 번 나온 것을 가릴 수 없어", first)
            self.assertNotIn("닮은 문제", first)
            tutor.debug("p1", self.BUGGY, self.FAILED)  # 함정 기록(wrong_init)
            tutor.store.put_problem("p2", "python", "주차장에 들어온 차 번호와 나간 차 번호가 주어진다. 아직 남은 차 한 대의 번호를 구하라.", title="주차장")
            fake.calls.clear()
            tutor.turn("p2", "chair", "start")
            second = fakes.prompt(fake, "plan.draft_blocks")
            self.assertIn("되풀이한 실수", second)  # 사용자에 대한 것은 쓴다
            self.assertIn("시작 값 잘못(1번)", second)
            self.assertEqual(fakes.tasks(fake).count("plan.abstract"), 1)
            self.assertNotIn("plan.gate", fakes.tasks(fake))  # p1은 열어만 봤다(제출한 적 없다): 후보가 아니다
            self.assertEqual(tutor.store.load("p2").plan.link, "")
            for task in ("plan.solve", "plan.draft_blocks"):  # 지난 문항의 흐름이 풀이와 블록 프롬프트에 없다
                self.assertNotIn("NEXT_SECRET", fakes.prompt(fake, task))
            # 풀이 가이드에는 패턴 지식도 넣지 않는다: 뼈대(패턴·기술·태그)와 불러온 참고를 바꿔도 풀이 프롬프트는 같다
            from dataclasses import replace

            from ..plan.prompts import solve_messages
            from ..state import Abstract
            plain = tutor.store.load("p2")
            known = {"ctx": replace(plain, patterns=["dup_names"], skills=["two_d_list"]), "strategy": "fresh", "recall": {"patterns": ["- 개수 세기(딕셔너리)"], "weak": ["시작 값 잘못"]},
                     "abstract": Abstract(spec="x", patterns=["dup_names"], tags=["count_map", "bfs"], level=3)}
            self.assertEqual(solve_messages(known), solve_messages({"ctx": replace(plain, patterns=[], skills=[]), "strategy": "fresh"}))
            tutor.store.add_submission("p1", "def solution(a, b): ...", False)  # 이제 풀어 본 문항이다
            tutor.store.put_problem("p3", "python", "놀이공원 이야기로 바꾼 같은 문제.", title="놀이공원")
            tutor.store.put_fact("p3", abstract["spec"], ["dup_names"])
            fake.calls.clear()
            tutor.turn("p3", "chair", "start")
            self.assertIn("지난 문제의 풀이 흐름: 입력받기 → NEXT_SECRET", fakes.prompt(fake, "plan.gate"))
            self.assertEqual(tutor.store.load("p3").plan.link, "추천 서가에 꽂히는 책: 입력받기 → NEXT_SECRET")  # 같은 구조라고 판정된 한 줄
            self.assertNotIn("NEXT_SECRET", fakes.prompt(fake, "plan.draft_blocks"))
            tutor.store.put_problem("p4", "python", "조건이 하나 다른 문제.", title="형제")
            tutor.store.put_fact("p4", abstract["spec"], ["dup_names"])
            tutor.turn("p4", "chair", "start")
            self.assertEqual(tutor.store.load("p4").plan.link, "")  # 판정이 N이면 남기지 않는다
        finally:
            tutor.close()

    @unittest.skipUnless(__import__("importlib").util.find_spec("qdrant_client"), "qdrant-client 없음")
    def test_vector_index_finds_similar_problem_without_shared_pattern(self):
        """패턴이 안 겹쳐도 명세가 닮으면 벡터 색인이 풀어 본 지난 문항을 후보로 올린다(판정을 통과해야 남는다). 색인은 새 계획 때 채워지고, 비면 원본에서 다시 채운다."""
        from ..knowledge.index import ProblemIndex, chargram_embedder

        spec = {"spec": "문자열 배열 둘. 한쪽에만 남는 원소 하나를 구한다. 같은 값 중복 가능.", "patterns": []}
        fake = FakeLlm({"plan.abstract": [spec, spec], "plan.draft_blocks": LINED["plan.draft_blocks"] * 2, "plan.solve": [SOLVED], "plan.gate": ["Y"]})
        index = ProblemIndex(str(Path(self.dir.name) / "vectors"), embed=chargram_embedder())
        tutor = Tutor(self.path, client=fake, index=index)
        try:
            tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
            tutor.store.put_problem("p2", "python", "주차장 이야기로 바꾼 같은 문제. " + fakes.PROBLEM, title="주차장")
            tutor.turn("p1", "chair", "start")
            self.assertEqual(index.count(), 1)
            tutor.store.add_submission("p1", "def solution(a, b): ...", True)
            fake.calls.clear()
            fake.scripts["plan.solve"] = [SOLVED]
            tutor.turn("p2", "chair", "start")
            self.assertEqual(tutor.store.load("p2").plan.link, "추천 서가에 꽂히는 책: 입력받기 → NEXT_SECRET")
            index.clear()  # 모델이 바뀌어 색인이 비었다고 치면
            self.assertEqual(tutor.reindex(), 2)
            self.assertEqual(index.count(), 2)
        finally:
            tutor.close()
            index.close()

    def test_user_method_is_followed_with_new_blocks(self):
        """설계: 사용자의 사고 방향이 먼저다. 계획과 다른 방법이 풀리면 그 방법으로 블록을 다시 짠다."""
        sort_blocks = [fakes.block(1, "두 명단 정렬", "REF_SORT", hints=["두 명단을 나란히 비교하려면 먼저 무엇을 해야 할까요?"]),
                       fakes.block(2, "앞에서부터 비교", "REF_CMP", "loop")]
        second = {**fakes.drafted([fakes.as_dict(b) for b in sort_blocks], "sort"), "followed": True}
        tutor, fake = self.tutor({"plan.draft_blocks": [DRAFT["plan.draft_blocks"][0], second],
                                  "chair.judge": ["[check]D g", "[check]N1 g"], "chair.ask": ["정렬하면 무엇이 나란히 놓일까요?"]})
        try:
            tutor.turn("p1", "chair", "start")
            got = tutor.turn("p1", "chair", "message", text="두 명단을 정렬해서 앞에서부터 비교하면 돼요")
            self.assertEqual(got.status, 200)
            self.assertTrue(got.body["messages"][-1]["text"].startswith("말한 방법으로 블록을 다시 짰어요."))
            self.assertTrue(got.body["messages"][-1]["text"].endswith(sort_blocks[0].hints[0]))
            self.assertEqual((got.body["open_count"], len(got.body["blocks"])), (1, 2))
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.plan.strategy, ctx.plan.algorithm, ctx.chair[-1].move), ("keep_flow", "sort", "replan"))
            self.assertIn("사용자가 말한 방법:\n두 명단을 정렬해서", fakes.prompt(fake, "plan.draft_blocks"))
            self.assertIn("지금 계획의 흐름: 입력받기(목표-입력받기) → NEXT_SECRET", fakes.prompt(fake, "plan.draft_blocks"))  # 같은 방법이면 다시 짜지 않게
            again = tutor.turn("p1", "chair", "message", text="음 잘 모르겠어요")  # 새 계획의 첫 블록에서 이어 간다(저장 힌트 하나를 이미 냈다)
            self.assertEqual(again.body["messages"][-1]["text"], HINTS_DONE_UNFOUND)
            self.assertEqual(fakes.tasks(fake).count("plan.draft_blocks"), 2)  # 한 문항에 다시 짜기는 한 번
        finally:
            tutor.close()

    def test_canonical_guide_is_kept_when_user_method_is_followed(self):
        """정석 가이드는 문제마다 하나로 고정한다. 사용자 방법으로 다시 짜도 덮어쓰지 않고, 그 계획을 지우면 정석 가이드로 돌아간다."""
        own_code = "def solution(a, b):\n    a = sorted(a)\n    b = sorted(b)\n    return a[-1]"
        own = {"approach": "두 명단을 정렬해 앞에서부터 견준다.", "steps": ["정렬한다", "견준다"], "code": own_code, "followed": True}
        own_draft = {**fakes.drafted([{**fakes.as_dict(b), "reference": "", "lines": span} for b, span in zip(fakes.hinted(), ([1, 3], [4, 4]))], "sort"), "followed": True}
        tutor, fake = self.tutor({"plan.solve": [SOLVED, own], "plan.draft_blocks": [LINED["plan.draft_blocks"][0], own_draft, LINED["plan.draft_blocks"][0]],
                                  "chair.judge": ["[check]D g"]})
        try:
            tutor.turn("p1", "chair", "start")
            got = tutor.turn("p1", "chair", "message", text="두 명단을 정렬해서 앞에서부터 비교하면 돼요")
            self.assertTrue(got.body["messages"][-1]["text"].startswith("말한 방법으로 블록을 다시 짰어요."))
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.plan.strategy, ctx.solution.code, ctx.canonical.code), ("keep_flow", own_code, CODE))
            self.assertEqual("\n".join(block.reference for block in ctx.plan.blocks), own_code)  # 블록은 사용자 방법의 코드를 나눈 것
            self.assertIn("지금 풀이 방향: 이름마다 몇 번 나왔는지", fakes.prompt(fake, "plan.solve"))  # 같은 방법이면 다시 풀지 않게
            with tutor.store.conn:  # 화면의 '처음부터'가 사용자 방법의 계획을 지운 것처럼
                tutor.store.conn.execute("DELETE FROM tutor_session WHERE problem_id='p1'")
                tutor.store.conn.execute("DELETE FROM message WHERE problem_id='p1'")
            self.assertEqual(tutor.store.load("p1").solution.code, CODE)
            fake.calls.clear()
            tutor.turn("p1", "chair", "start")
            self.assertEqual(fakes.tasks(fake), ["plan.draft_blocks"])  # 정석 가이드를 다시 만들지 않고 그것으로 블록만 다시 짠다
            self.assertEqual("\n".join(block.reference for block in tutor.store.load("p1").plan.blocks), CODE)
        finally:
            tutor.close()

    def test_wrong_user_method_keeps_plan(self):
        rejected = {**fakes.drafted([fakes.as_dict(b) for b in fakes.hinted()]), "followed": False}
        tutor, fake = self.tutor({"plan.draft_blocks": [DRAFT["plan.draft_blocks"][0], rejected],
                                  "chair.judge": ["[check]D g"], "chair.ask": ["그 방법은 이름이 두 번 나올 때도 될까요?"]})
        try:
            tutor.turn("p1", "chair", "start")
            got = tutor.turn("p1", "chair", "message", text="돌려받은 목록에 이름이 있는지만 보면 돼요")
            self.assertEqual(got.body["messages"][-1]["text"], "그 방법은 이름이 두 번 나올 때도 될까요?")
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.plan.strategy, ctx.open_count, ctx.chair[-1].move), ("fresh", 1, "assume"))
        finally:
            tutor.close()

    BUGGY = "def solution(a, b):\n    count = {}\n    for name in a:\n        count[name] = 1\n    return count"
    FAILED = {"status": "failed", "cases": [{"id": "1", "input": '[["tom", "tom"], ["tom"]]', "expected": '"tom"', "got": "{'tom': 1}", "status": "failed"}]}
    FOUND = {"kind": "logic", "line": 4, "cause": "횟수를 늘리지 않고 늘 1을 넣는다", "fixed_line": "count[name] = count.get(name, 0) + 1", "pitfall": "wrong_init"}

    def test_debug_ladder_asks_without_giving_the_fix(self):
        """생각하는 의자의 디버깅: 증상 → 값 따라가기 → 줄 → 원인. 고친 줄은 말하지 않는다."""
        tutor, fake = self.tutor({"debug.locate": [self.FOUND], "debug.judge": ["[check]N", "[check]N", "[check]Y"],
                                  "debug.ask": ["tom이 두 번째로 나올 때 count는 어떻게 바뀌나요?",
                                                "4번째 줄을 count[name] = count.get(name, 0) + 1 로 바꾸면 될까요?",
                                                "늘 1을 넣는다는 걸 짚었네요. 그 줄이 해야 할 일을 말로 써 보면 어떻게 될까요?"]})
        try:
            start = tutor.debug("p1", self.BUGGY, self.FAILED)
            self.assertEqual((start.status, start.body["step"], start.body["line"], start.body["kind"]), (200, "symptom", None, "logic"))
            self.assertIn('solution(["tom", "tom"], ["tom"])의 기대한 값은 "tom"인데', start.body["messages"][-1]["text"])
            self.assertEqual(fakes.tasks(fake), ["debug.locate"])  # 증상 질문은 정해진 글(모델 0회)
            self.assertIn("wrong_init: 시작 값 잘못", fakes.prompt(fake, "debug.locate"))  # 온톨로지 함정 후보
            trace = tutor.debug("p1", self.BUGGY, self.FAILED, text="잘 모르겠어요")
            self.assertEqual((trace.body["step"], trace.body["line"]), ("trace", None))
            line = tutor.debug("p1", self.BUGGY, self.FAILED, text="count가 1이에요")
            self.assertEqual((line.body["step"], line.body["line"]), ("line", 4))
            self.assertNotIn("count.get", line.body["messages"][-1]["text"])  # 고친 줄이 새면 대체 질문
            self.assertIn("4번째 줄", line.body["messages"][-1]["text"])
            done = tutor.debug("p1", self.BUGGY, self.FAILED, text="아, 4번째 줄이 늘 1을 넣어서 두 번 나와도 1이네요")
            self.assertEqual((done.body["step"], done.body["line"]), ("fix", 4))
            self.assertEqual(done.body["messages"][-1]["text"], "그 줄이 해야 할 일을 말로 써 보면 어떻게 될까요?")  # 되받는 첫 문장('…짚었네요.')은 지운다
            self.assertEqual(fakes.tasks(fake).count("debug.locate"), 1)  # 같은 코드는 다시 진단하지 않는다
            self.assertEqual(fakes.tasks(fake).count("debug.ask"), 3)
            self.assertEqual(len(tutor.session("p1").body["debug"]), 7)
            self.assertEqual(tutor.session("p1").body["chair"], [])  # 의자 대화와 섞이지 않는다
            tutor.store.put_problem("p2", "python", fakes.PROBLEM)
            self.assertEqual(tutor.store.load("p2").frequent_pitfalls, [("wrong_init", 1)])  # 제출 → 함정 엣지가 다른 문항에서 보인다
        finally:
            tutor.close()

    KEY_TRAP = {"id": "python.missing_key", "what": "없는 키를 읽으면 멈춰요.", "fix": "`get(키, 0)`으로 읽어요.", "code": [], "right": [".get("], "fails": {"1": "failed"}, "outs": {"1": "{'tom': 1}"}}
    ROWS_TRAP = {"id": "python.shared_rows", "what": "모든 줄이 같은 목록이에요.", "fix": "줄마다 새 목록을 만들어요.", "code": [], "right": ["for _ in range"], "fails": {"9": "failed"}, "outs": {"9": "1"}}

    def test_debug_picks_lang_trap_and_feedback_follows(self):
        """증명된 언어 함정: 실패와 맞는 것만 후보로 내놓고(캐시 앞부분 밖), 모델이 고른 것을 원인 설명 단계에서 무슨 일이 일어나는지(what)만 말한다.
        피드백은 디버그가 고른 것을 받는다: 실패한 제출엔 what만, 통과한 뒤에는 고치는 법(fix)까지. 모델 호출 수는 그대로다."""
        analysis = {"analysis": "같은 이름이 둘이면요?", "similar_hint": "센다", "advice": "센 값을 보세요."}
        fake = FakeLlm({**DRAFT, "debug.locate": [{**self.FOUND, "trap": "python.missing_key"}], "debug.judge": ["[check]N"] * 4,
                        "debug.ask": ["count는 어떻게 바뀌나요?", "그 줄은 무엇을 하나요?", "그 줄을 어떻게 바꿀까요?", "다시 볼까요?"],
                        "feedback.assess": ["[check]30 Y"] * 4, "feedback.analyze": [analysis] * 4})
        tutor = Tutor(self.path, client=fake, shape=lambda _pid, _language: {"traps": [self.KEY_TRAP, self.ROWS_TRAP]})
        try:
            tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
            tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
            tutor.debug("p1", self.BUGGY, self.FAILED)
            locate = [c for c in fake.calls if c["task"] == "debug.locate"][0]["messages"][-1]
            self.assertIn("- python.missing_key: 없는 키를 읽으면 멈춰요.", locate["content"])
            self.assertNotIn("python.shared_rows", locate["content"])  # 떨어진 케이스가 다르다
            self.assertGreater(locate["content"].index("trap:"), locate["cache_prefix"])  # 실패마다 다른 글은 캐시 앞부분 밖
            self.assertEqual(tutor.store.load("p1").debug_state.trap, "python.missing_key")
            said = [tutor.debug("p1", self.BUGGY, self.FAILED, text="모르겠어요").body["messages"][-1]["text"] for _ in range(4)]  # trace, line, cause, cause
            self.assertEqual([text.startswith("없는 키를 읽으면 멈춰요.") for text in said], [False, False, True, False])  # 원인 설명에 처음 왔을 때만
            self.assertFalse(any("get(키, 0)" in text for text in said))  # 고치는 법은 말하지 않는다
            self.assertEqual(fakes.tasks(fake).count("debug.locate"), 1)

            tutor.store.add_submission("p1", self.BUGGY, False)
            self.assertEqual(tutor.feedback("p1").body["advice"], "센 값을 보세요. 없는 키를 읽으면 멈춰요.")
            tutor.store.add_submission("p1", CODE + "\n    return []", False)  # 고친 꼴의 이름이 있으면 그 함정은 이 실패의 원인이 아니다
            self.assertEqual(tutor.feedback("p1").body["advice"], "센 값을 보세요.")
            tutor.store.add_submission("p1", CODE, True)
            self.assertEqual(tutor.feedback("p1").body["advice"], "센 값을 보세요. 없는 키를 읽으면 멈춰요. `get(키, 0)`으로 읽어요.")
            tutor.store.add_submission("p1", CODE.replace("count.get(name, 0) + 1", "(count[name] if name in count else 0) + 1"), True)  # 그 꼴을 고친 흔적 없이 다른 방식으로 통과
            self.assertEqual(tutor.feedback("p1").body["advice"], "센 값을 보세요.")
            self.assertEqual(fakes.tasks(fake).count("feedback.analyze"), 4)
            self.assertNotIn("없는 키", fakes.prompt(fake, "feedback.analyze"))  # 글은 엔진이 붙인다
        finally:
            tutor.close()

    def test_debug_drops_unlisted_trap_and_stays_off_without_data(self):
        """모델이 내놓지 않은 id를 고르면 버린다. 자료가 없거나 맞는 후보가 없으면 프롬프트는 그대로다."""
        listed = {"traps": [self.KEY_TRAP, self.ROWS_TRAP]}
        other = {"traps": [{**self.KEY_TRAP, "fails": {"1": "runtime_error"}}]}  # 같은 케이스, 다른 상태
        for n, (shape, trap) in enumerate(((listed, "python.shared_rows"), (other, "python.missing_key"), ({"traps": []}, "python.missing_key"), (None, "python.missing_key"))):
            fake = FakeLlm({"debug.locate": [{**self.FOUND, "trap": trap}]})
            tutor = Tutor(str(Path(self.dir.name) / f"off{n}.db"), client=fake, shape=None if shape is None else lambda _pid, _language, s=shape: s)
            try:
                tutor.store.put_problem("p1", "python", fakes.PROBLEM)
                tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
                tutor.debug("p1", self.BUGGY, self.FAILED)
                self.assertEqual(tutor.store.load("p1").debug_state.trap, "", (shape, trap))
            finally:
                tutor.close()
            if shape != listed:  # 맞는 후보가 없으면 프롬프트에 후보 줄이 없다
                self.assertNotIn("trap:", fakes.prompt(fake, "debug.locate"))

    def test_debug_candidates_follow_the_language(self):
        """진단 후보 목록에 파이썬에만 있는 실수(콜론 빠짐)가 다른 언어로 풀 때 들어가지 않는다. 파이썬에는 그대로 들어간다."""
        tutor, fake = self.tutor({"debug.locate": [self.FOUND, self.FOUND]})
        try:
            tutor.store.put_problem("pj", "java", fakes.PROBLEM, title="자바 문제")
            tutor.store.put_fact("pj", "문자열 배열 둘, 남는 원소 하나", [])
            tutor.debug("p1", self.BUGGY, self.FAILED)
            python = fakes.prompt(fake, "debug.locate")
            fake.calls.clear()
            tutor.debug("pj", self.BUGGY, self.FAILED)
            java = fakes.prompt(fake, "debug.locate")
            self.assertIn("missing_colon: 콜론(:) 빠짐", python)
            self.assertIn("no_return: 돌려주지 않음(None)", python)
            self.assertNotIn("missing_colon", java)
            self.assertNotIn("indent:", java)
            self.assertIn("no_return: 돌려주지 않음 —", java)
            self.assertNotIn("None", java)
        finally:
            tutor.close()

    def test_weak_pitfalls_follow_the_language(self):
        """다른 언어로 바꾼 사용자에게 파이썬에만 있는 실수 이름('콜론 빠짐')을 되풀이한 실수로 보여 주지 않는다."""
        from ..common.talk_prompts import weak_pitfalls
        for language, want in (("python", ["콜론(:) 빠짐(3번)", "돌려주지 않음(None)(2번)"]), ("java", ["돌려주지 않음(2번)"])):
            ctx = fakes.context(language=language, frequent_pitfalls=[("missing_colon", 3), ("no_return", 2)])
            self.assertEqual(weak_pitfalls(ctx), want, language)

    def test_debug_first_question_uses_clue_and_refuses_answer(self):
        """첫 질문이 늘 '코드 첫 줄부터 손으로 따라가 보면…'이었다. 진단이 함께 지은 첫 질문(실패 입력과 코드의 단서)을 증상 뒤에 붙인다(모델 호출은 그대로 1번).
        '그냥 답 알려줘요'에는 거절 없이 다음 질문으로 넘어갔다: 거절과 대안(볼 곳을 좁힌다)을 분명히 말한다."""
        from ..debug.prompts import OPENING_RULE
        from ..debug.rules import ANSWER_LEAD, symptom, symptom_question

        clue = "입력에 tom이 두 번 있는데, 두 번째 tom을 만났을 때 count에는 무엇이 들어가나요?"
        tutor, fake = self.tutor({"debug.locate": [{**self.FOUND, "opening": clue}],
                                  "debug.ask": ["tom이 두 번째로 나올 때 count는 어떻게 바뀌나요?", "그 값은 두 번째 tom 뒤에 어떻게 되나요?"],
                                  "debug.judge": ["[check]A"]})
        try:
            start = tutor.debug("p1", self.BUGGY, self.FAILED)
            self.assertEqual(start.body["messages"][-1]["text"], f"{symptom(self.FAILED)} {clue}")
            self.assertEqual(fakes.tasks(fake), ["debug.locate"])  # 첫 질문은 진단과 한 번에 받는다
            self.assertIn(OPENING_RULE, fakes.prompt(fake, "debug.locate"))
            short = tutor.debug("p1", self.BUGGY, self.FAILED, text="그냥 답 알려줘요")
            self.assertEqual(short.body["messages"][-1]["text"], ANSWER_LEAD + "tom이 두 번째로 나올 때 count는 어떻게 바뀌나요?")
            self.assertEqual((short.body["step"], fakes.tasks(fake).count("debug.judge")), ("trace", 0))  # 짧은 답 요청은 규칙으로 가른다. 한 단계 좁힌다
            ask = [c for c in fake.calls if c["task"] == "debug.ask"][-1]["messages"][-1]["content"]
            self.assertIn("고친 코드나 답을 달라고 했다", ask)
            self.assertNotIn("사용자 말:", ask)
            long = tutor.debug("p1", self.BUGGY, self.FAILED, text="시간이 없어서 그러는데 고친 코드를 통째로 보여 주실 수 있나요")
            self.assertTrue(long.body["messages"][-1]["text"].startswith(ANSWER_LEAD))  # 판정이 A로 가른 긴 요청도 같다
            self.assertIn("[check]A", fakes.prompt(fake, "debug.judge"))
        finally:
            tutor.close()
        leaked = ("4번째 줄에서 count에 무엇이 들어가나요?", "count[name] = count.get(name, 0) + 1 로 바꾸면 될까요?", "", "두 번째 tom을 보세요.",
                  # 고친 줄의 조각, 줄 번호의 다른 꼴도 첫 질문에서는 막는다
                  "count.get(name, 0) + 1로 바꾸면 두 번째 tom은 어떻게 될까요?", "4줄에서 count에 1을 넣지 말고 무엇을 넣어야 할까요?",
                  "네 번째 줄에서 count에 하나를 더해야 하지 않을까요?", "4행을 보면 무엇이 보이나요?", "line 4에서 count는 몇이 되나요?")
        for n, opening in enumerate(leaked):
            tutor, fake = self.tutor({"debug.locate": [{**self.FOUND, "opening": opening}]})
            try:
                got = tutor.debug("p1", f"{self.BUGGY}  # {n}", self.FAILED).body["messages"][-1]["text"]  # 코드가 달라야 새로 진단한다
                self.assertEqual(got, symptom_question(self.FAILED), opening)  # 줄 번호·고친 줄·질문 아님은 정해진 글로
            finally:
                tutor.close()

    def test_debug_new_code_restarts_and_syntax_shows_line(self):
        syntax = {"status": "runtime_error", "cases": [{"id": "1", "input": "[[1]]", "expected": "1", "got": "", "status": "runtime_error",
                  "error": '  File "solution.py", line 3\n    for name in a\n                 ^\nSyntaxError: expected \':\''}]}
        found = {"kind": "logic", "line": 99, "cause": "for 줄 끝에 콜론이 없다", "fixed_line": "    for name in a:", "pitfall": "missing_colon"}
        tutor, fake = self.tutor({"debug.locate": [self.FOUND, found], "debug.ask": ["3번째 줄 끝에 무엇이 빠졌을까요?"]})
        try:
            tutor.debug("p1", self.BUGGY, self.FAILED)
            got = tutor.debug("p1", self.BUGGY.replace("in a:", "in a"), syntax)
            self.assertEqual((got.body["step"], got.body["kind"], got.body["line"]), ("error", "syntax", 3))  # 종류와 줄은 오류 글이 정한다
            self.assertEqual(fakes.tasks(fake).count("debug.locate"), 2)
            self.assertEqual(tutor.debug("p1", "x = 1", {"status": "passed"}).status, 400)
            self.assertEqual(tutor.debug("p1", " ", self.FAILED).status, 400)
        finally:
            tutor.close()

    def test_debug_keeps_user_words_after_code_change_and_marks_line_found_first(self):
        """고친 뒤 보낸 말이 사라졌다, 사용자가 먼저 줄을 말하면 짚은 줄 표시가 나오지 않았다."""
        tutor, fake = self.tutor({"debug.locate": [self.FOUND, self.FOUND], "debug.judge": ["[check]Y"],
                                  "debug.ask": ["4번째 줄을 어떻게 바꾸면 두 번째 tom도 셀 수 있을까요?", "다시 돌려 보면 tom은 몇 번 세어질까요?"]})
        try:
            tutor.debug("p1", self.BUGGY, self.FAILED)
            found = tutor.debug("p1", self.BUGGY, self.FAILED, text="4번째 줄이 늘 1을 넣어요")
            self.assertEqual((found.body["step"], found.body["line"]), ("fix", 4))  # line 단계를 건너뛰어도 줄을 싣는다
            changed = tutor.debug("p1", self.BUGGY.replace("= 1", "= 2"), self.FAILED, text="고쳤어요")
            self.assertEqual((changed.body["messages"][-2]["role"], changed.body["messages"][-2]["text"]), ("user", "고쳤어요"))
            self.assertIn("고쳤어요", [m["text"] for m in tutor.session("p1").body["debug"]])
        finally:
            tutor.close()

    def test_debug_timeout_gets_size_rule_as_reference(self):
        """시간 초과이고 입력 크기를 알면 경험칙 한 줄을 참고로 붙인다. 틀린 답일 때는 붙이지 않는다."""
        tutor, fake = self.tutor({"debug.locate": [self.FOUND, self.FOUND]})
        try:
            tutor.store.put_fact("p1", "이름 세기", [], size=100000)
            tutor.debug("p1", self.BUGGY, self.FAILED)
            self.assertNotIn("입력 크기 경험칙", fakes.prompt(fake, "debug.locate"))
            tutor.debug("p1", self.BUGGY + "\n", {"status": "timeout", "cases": [{"id": "1", "input": "[[1]]", "expected": "1", "got": "", "status": "timeout"}]})
            self.assertIn("입력 크기 경험칙", fake.calls[-1]["messages"][-1]["content"])
        finally:
            tutor.close()

    def test_block_state_per_problem_and_cleared_by_new_plan(self):
        tutor, fake = self.tutor({**DRAFT, "chair.check_code": ["[check]N1"], "chair.ask": ["이 코드에서 무엇이 빠졌을까요?"] * 2})
        try:
            tutor.store.put_problem("p2", "python", fakes.PROBLEM)
            tutor.turn("p1", "chair", "start")
            tutor.turn("p1", "chair", "block_filled", block_id="b1", code="x = 1")
            again = tutor.turn("p1", "chair", "block_filled", block_id="b1", code="\nx = 1 ")  # 앞 빈 줄·끝 공백만 다르다(첫 줄 들여쓰기는 다른 코드다)
            self.assertTrue(again.body["messages"][-1]["text"].startswith("이 블록은 실행하지 못해서("))  # 읽고 거절했다: '확인 전'이다
            self.assertEqual(fakes.tasks(fake).count("chair.check_code"), 1)  # 같은 코드는 모델 0회
            row = tutor.store.conn.execute("SELECT tries FROM block_state WHERE problem_id='p1' AND block_id='b1'").fetchone()
            self.assertEqual(row[0], 0)  # 채점 함수 없이 읽고 낸 거절은 (같은 코드를 다시 보내도) 틀린 수에 넣지 않는다
            self.assertIsNone(tutor.store.conn.execute("SELECT 1 FROM block_state WHERE problem_id='p2'").fetchone())
            with self.assertRaises(sqlite3.IntegrityError):
                with tutor.store.conn:
                    tutor.store.conn.execute("INSERT INTO block_state(problem_id, block_id, code, code_hash, verdict, at) VALUES('nope','b1','','','Y','t')")
        finally:
            tutor.close()

    def test_solution_guide_is_checked_by_the_judge_and_blocks_tile_its_code(self):
        """풀이 가이드: 정답 코드를 채점기로 확인하고(틀리면 결과를 돌려주고 다시), 블록의 참고 코드는 그 코드의 줄 구간 그대로다."""
        seen = []

        def check(problem_id, code):
            seen.append((problem_id, code))
            ok = "count.get" in code
            return {"status": "passed" if ok else "failed",
                    "cases": [] if ok else [{"id": "1", "input": '[["a", "a"], ["a"]]', "expected": '"a"', "got": "{}", "status": "failed"}]}

        wrong = {**SOLVED, "code": "```python\ndef solution(a, b):\n    return {}\n```"}
        fake = FakeLlm({"plan.solve": [wrong, SOLVED], **LINED, "explain.write": [{"sections": [*fakes.SECTIONS[:3], {"title": "블록별 설명", "body": "설명\n```python\n바뀐 코드\n```"}]}]})
        tutor = Tutor(self.path, client=fake, check=check)
        try:
            tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
            tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
            self.assertEqual(tutor.prepare("p1").status, 200)
            ctx = tutor.store.load("p1")
            self.assertEqual((ctx.solution.code, ctx.solution.verified, ctx.solution.steps), (CODE, True, SOLVED["steps"]))
            self.assertEqual(ctx.solution.clues, SOLVED["clues"])  # 단서: 문제의 어떤 말에서 무엇을 읽는가
            self.assertIn("단서(문제 글의 어디에서 무엇을 읽는가", fakes.prompt(fake, "plan.draft_blocks"))
            self.assertEqual(seen, [("p1", "def solution(a, b):\n    return {}"), ("p1", CODE)])  # 코드 울타리는 벗겨서 채점한다
            again = fake.calls[1]["messages"][-1]["content"]
            self.assertIn("앞서 쓴 코드는 채점에서 틀렸다", again)
            self.assertIn('solution(["a", "a"], ["a"])의 기대한 값은 "a"인데', again)
            self.assertEqual("\n".join(block.reference for block in ctx.plan.blocks), CODE)  # 블록을 이으면 정답 코드다
            self.assertIn(" 1| def solution(a, b):", fakes.prompt(fake, "plan.draft_blocks"))
            solve = fakes.prompt(fake, "plan.solve")
            self.assertNotIn("참고 —", solve)  # 풀이 가이드에는 불러온 지식을 넣지 않는다
            body = tutor.explain("p1").body["explain"]["sections"][-1]["body"]
            self.assertIn(f"```python\n{CODE}\n```", body)  # 해설의 전체 코드는 가이드 코드 그대로다
            self.assertNotIn("바뀐 코드", body)
            self.assertIn("정답 코드(그대로 보여 주지 않는다)", fakes.prompt(fake, "explain.write"))
        finally:
            tutor.close()

    def crossed(self, scripts, results, check=None):
        """정답 풀이 대조를 가짜 실행기로: results는 cross.run이 차례로 낼 결과. (튜터, 가짜 모델, 실행기 기록)."""
        seen = {"runs": [], "done": []}

        def run(pid, code, brute, maker, bounds):
            seen["runs"].append((code, brute, maker, bounds))
            return results.pop(0)

        cross = mock.Mock(mode=lambda pid: "function", run=run, done=lambda pid, verdict: seen["done"].append(verdict))
        fake = FakeLlm(scripts)
        tutor = Tutor(self.path, client=fake, check=check or (lambda pid, code: {"status": "passed", "cases": []}), cross=cross)
        tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
        tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
        return tutor, fake, seen

    BRUTE = {"code": "```python\ndef solution(a, b):\n    return [x for x in a if a.count(x) > b.count(x)][0]\n```"}
    MAKER = {"code": "def small():\n    return [[['a'], []]]\ndef edge():\n    return []\ndef large():\n    return []", "bounds": [{"arg": 0, "shortest": 1, "longest": 100000}]}

    def test_cross_check_agrees_and_keeps_the_guide(self):
        """대조가 맞으면 가이드를 그대로 쓰고 결과(모두 통과, 숨은 케이스 수, 호출 2회, 처음 풀이의 급만)를 남긴다. 단순 풀이·생성기 코드의 울타리는 벗겨 실행기에 넘긴다."""
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], "plan.brute": [self.BRUTE], "plan.cases": [self.MAKER], **LINED},
                                         [{"status": "same", "hidden": 12, "efficiency": 2}])
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.brute", "plan.cases", "plan.draft_blocks"])
            self.assertEqual(tutor.store.load("p1").solution.code, CODE)
            code, brute, maker, bounds = seen["runs"][0]
            self.assertEqual((code, brute.startswith("def solution"), bounds[0].longest), (CODE, True, 100000))
            self.assertEqual({k: seen["done"][0][k] for k in ("verified", "calls", "tiers", "hidden", "efficiency")},
                             {"verified": "all", "calls": 2, "tiers": ["small"], "hidden": 12, "efficiency": 2})
            self.assertIn("정의 그대로 푸는 검산자", fakes.prompt(fake, "plan.brute") + fake.calls[1]["messages"][0]["content"])
        finally:
            tutor.close()

    def test_cross_check_resolves_once_per_tier_then_gives_up(self):
        """대조가 다르면 그 입력을 보여 주며 가운데 급으로 한 번, 그래도 다르면 큰 급으로 한 번만 다시 푼다. 끝내 다르면 '검증하지 못함'이고
        더 쓴 호출은 상한(5) 안이다. 다시 푼 코드도 공개 예시를 통과해야 쓴다."""
        differ = {"status": "differ", "input": '[["a", "b"], ["b"]]', "got": '"b"', "want": '"a"'}
        other = {**SOLVED, "code": CODE.replace("count = {}", "count = dict()")}  # 줄 수가 같아 같은 블록 초안으로 나뉜다
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED, other, other], "plan.brute": [self.BRUTE], "plan.cases": [self.MAKER], **LINED},
                                         [differ, differ, differ])
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.brute", "plan.cases", "plan.solve", "plan.solve", "plan.draft_blocks"])
            models = [c["params"]["model"] for c in fake.calls if c["task"] == "plan.solve"]
            self.assertEqual([next(s for s in ("haiku", "sonnet", "opus") if s in m) for m in models], ["haiku", "sonnet", "opus"])  # 기본(작음) → 가운데 급 한 번 → 큰 급 한 번
            self.assertIn('입력: [["a", "b"], ["b"]]', fake.calls[3]["messages"][-1]["content"])  # 다른 입력과 두 결과를 보여 준다
            self.assertIn('느린 풀이의 결과: "a"', fake.calls[3]["messages"][-1]["content"])
            done = seen["done"][0]
            self.assertEqual((done["verified"], done["tiers"], done["calls"]), ("none", ["small", "middle", "large"], 4))
            self.assertLessEqual(done["calls"], 5)
            self.assertEqual(len(seen["runs"]), 3)
            self.assertEqual(tutor.store.load("p1").solution.code, other["code"])  # 예시를 통과한 마지막 풀이
        finally:
            tutor.close()

    def test_cross_check_takes_the_resolved_code_when_it_agrees(self):
        fixed = {**SOLVED, "code": CODE.replace("count = {}", "count = dict()")}
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED, fixed], "plan.brute": [self.BRUTE], "plan.cases": [self.MAKER], **LINED},
                                         [{"status": "differ", "input": "[]", "got": "1", "want": "2"}, {"status": "same", "hidden": 3, "efficiency": 0}])
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(tutor.store.load("p1").solution.code, fixed["code"])
            self.assertEqual((seen["runs"][1][0], seen["done"][0]["verified"], seen["done"][0]["tiers"]), (fixed["code"], "all", ["small", "middle"]))
        finally:
            tutor.close()

    def test_cross_check_on_the_provider_path_reads_bounds_and_climbs_tiers(self):
        """가짜 모델이 아니라 공급자 경로(app.llm의 요청·응답 읽기)로: 생성기의 제한사항(low·high가 든 bounds)을 읽어 실행기에 넘기고,
        대조가 계속 다르면 기본(작음) → 가운데 → 큼 차례로 Haiku → Sonnet → Opus를 부른다. 네트워크는 쓰지 않는다(전송을 바꿔 끼운다)."""
        from dataclasses import asdict, is_dataclass

        from ..llm import client
        client._backend_session()  # 저장소 루트를 경로에 더해 app.llm을 부른다
        from app.llm.wire import set_transport

        maker = {**self.MAKER, "bounds": [{"arg": 0, "low": 1, "high": 100, "shortest": 1, "longest": 100000}]}
        replies = {"plan.solve": [SOLVED] * 3, "plan.brute": [self.BRUTE], "plan.cases": [maker],
                   "plan.draft_blocks": [asdict(b) if is_dataclass(b) else b for b in LINED["plan.draft_blocks"]]}
        now, asked = {"task": ""}, []
        backend = client._backend_use

        def tracked(model, messages, schema, *, task=None, **params):
            now["task"] = task
            return backend(model, messages, schema, task=task, **params)

        def transport(url, headers, body, timeout):
            asked.append((now["task"], body["model"]))
            got = replies[now["task"]]
            return {"content": [{"type": "text", "text": json.dumps(got.pop(0) if len(got) > 1 else got[0], ensure_ascii=False)}], "stop_reason": "end_turn", "usage": {}}

        seen = {"runs": [], "done": []}

        def run(pid, code, brute, maker_code, bounds):
            seen["runs"].append(bounds)
            return {"status": "differ", "input": "[]", "got": "1", "want": "2"}

        cross = mock.Mock(mode=lambda pid: "function", run=run, done=lambda pid, verdict: seen["done"].append(verdict))
        env = {"ANTHROPIC_API_KEY": "test", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": "", "ALGOBLOCK_THEME_GUIDE": "", "ALGOBLOCK_THEME_INGEST": "",
               "ALGOBLOCK_THEME_BLOCKS": "", "ALGOBLOCK_LLM_USAGE_LOG": "", "ALGOBLOCK_LLM_PROMPT_DIR": ""}
        set_transport(transport)
        self.addCleanup(set_transport, None)
        with mock.patch.dict("os.environ", env), mock.patch.object(client, "_backend_use", tracked):
            tutor = Tutor(self.path, check=lambda pid, code: {"status": "passed", "cases": []}, cross=cross)
            try:
                tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
                tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
                self.assertEqual(tutor.prepare("p1").status, 200)
            finally:
                tutor.close()
        self.assertEqual([model for task, model in asked if task == "plan.solve"], ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"])
        self.assertEqual([(b.arg, b.low, b.high, b.shortest, b.longest) for b in seen["runs"][0]], [(0, 1, 100, 1, 100000)])
        self.assertEqual((seen["done"][0]["verified"], seen["done"][0]["tiers"]), ("none", ["small", "middle", "large"]))

    def test_cross_check_skips_when_examples_never_pass(self):
        """공개 예시를 끝내 통과하지 못하면 대조하지 않고(모델 0회 더) 그 예시를 '확인이 필요한 곳'으로 남긴다(문제를 잘못 읽었을 수 있다)."""
        failed = {"status": "failed", "cases": [{"id": "1", "kind": "example", "status": "passed"}, {"id": "2", "kind": "example", "status": "failed",
                                                                                                    "input": "[]", "expected": "1", "got": "2"}]}
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED] * 3, **LINED}, [], check=lambda pid, code: failed)
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve"] * 3 + ["plan.draft_blocks"])
            self.assertEqual((seen["runs"], seen["done"][0]["verified"], seen["done"][0]["doubts"]),
                             ([], "none", [{"where": "예시 2", "note": "기대 결과와 풀이가 맞지 않음"}]))
        finally:
            tutor.close()

    def test_guide_check_has_three_outcomes(self):
        """풀이 가이드의 확인은 통과(True)·통과하지 못함(False)·채점하지 못함(None) 셋이다. 채점하지 못하면(도구·케이스 없음, 인자 형 미지원) 다시 쓰게 하지 않고
        (모델 1회), 저장했다가 읽어도 구별되며, 등록 화면의 글은 풀이가 틀렸다고 하지 않고 까닭을 말한다."""
        for status, want, solves in (("passed", True, 1), ("failed", False, 3), ("compile_error", False, 3), ("entry_missing", False, 3),
                                     ("toolchain_missing", None, 1), ("unsupported_signature", None, 1), ("no_cases", None, 1)):
            self.path = str(Path(self.dir.name) / f"{status}.db")  # 상태마다 새 저장소(정석 가이드는 한 번 저장되면 다시 풀지 않는다)
            tutor, fake, seen = self.crossed({"plan.solve": [SOLVED] * 3, "plan.brute": [self.BRUTE], "plan.cases": [self.MAKER], **LINED}, [{"status": "same"}],
                                             check=lambda pid, code, status=status: {"status": status, "cases": []})
            try:
                self.assertEqual(tutor.prepare("p1").status, 200)
                self.assertEqual(fakes.tasks(fake).count("plan.solve"), solves, status)
                self.assertIs(tutor.store.load("p1").solution.verified, want, status)  # 저장했다가 읽어도 같다
                if want is None:
                    why = seen["done"][0]["why"]
                    self.assertTrue(why.startswith("튜터의 풀이를 확인하지 못했어요."), why)
                    self.assertEqual(("통과하지 못했어요" in why, "설치하면" in why), (False, status == "toolchain_missing"))
                    self.assertEqual((seen["runs"], seen["done"][0]["verified"], seen["done"][0]["doubts"]), ([], "none", []))
            finally:
                tutor.close()

    def test_abstract_labels_level_and_tags(self):
        """분석 호출이 단계(1~5)와 태그(온톨로지 기법 id만)를 함께 붙여 뼈대에 둔다(새 호출 없이)."""
        spec = {"spec": "문자열 배열 둘", "patterns": [], "size": 0, "skills": [], "level": 4, "tags": ["count_map", "지어낸 낱말", "count_map", "sort_scan"]}
        tutor, fake = self.tutor({"plan.abstract": [spec], "plan.solve": [SOLVED], **LINED})
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(tutor.store.labels()["p1"], {"level": 4, "tags": ["count_map", "sort_scan"]})
            self.assertIn("4: 알고리즘 둘을 엮거나 상태 설계가 필요하다", fakes.prompt(fake, "plan.abstract"))
        finally:
            tutor.close()

    def test_recheck_crosses_an_old_guide_once(self):
        """대조 없이 준비해 둔 가이드(대조 기능 전에 등록): recheck가 대조만 한다. 맞으면 None(계획 그대로), 다시 푼 코드가 맞으면 새 가이드."""
        tutor, fake, seen = self.crossed({"plan.solve": [SOLVED], **LINED, "plan.brute": [self.BRUTE] * 2, "plan.cases": [self.MAKER] * 2},
                                         [{"status": "same", "hidden": 1, "efficiency": 0}])
        try:
            tutor.cross = None  # 처음 준비는 대조 없이(예전처럼)
            self.assertEqual(tutor.prepare("p1").status, 200)
            tutor.cross = mock.Mock(mode=lambda pid: "function", run=lambda *args: {"status": "same", "hidden": 1, "efficiency": 0},
                                    done=lambda pid, verdict: seen["done"].append(verdict))
            self.assertIsNone(tutor.recheck("p1"))
            self.assertEqual(seen["done"][-1]["verified"], "all")
            self.assertEqual(fakes.tasks(fake)[-2:], ["plan.brute", "plan.cases"])
        finally:
            tutor.close()

    def test_blocks_must_cover_the_guide_code_in_order(self):
        """블록의 줄 구간이 가이드 코드를 빠짐없이 순서대로 나누지 않으면 한 번 다시 받는다. 그래도 아니면 규칙으로 자르고(rule_cut)
        이름·목표·질문만 한 번 받는다. 그것도 실패하면 종류에서 만든 일반 문구다(준비 전체가 실패했다)."""
        gap = fakes.drafted([{**fakes.as_dict(b), "reference": "", "lines": span} for b, span in zip(fakes.hinted(), ([1, 1], [4, 4]))])
        named = {"blocks": [{"id": f"b{n}", "name": f"이름{n}", "goal": f"목표{n}", "checks": [f"신호{n}"], "hints": []} for n in (1, 2, 3)]}
        tutor, fake = self.tutor({"plan.solve": [SOLVED, SOLVED, SOLVED], "plan.draft_blocks": [gap, LINED["plan.draft_blocks"][0], gap, gap, gap, gap],
                                  "plan.hints": [named]})
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks", "plan.draft_blocks"])
            self.assertFalse(tutor.store.load("p1").solution.verified)  # 채점기가 없으면 확인하지 못한 가이드다
            for pid in ("p2", "p3"):
                tutor.store.put_problem(pid, "python", fakes.PROBLEM)
                tutor.store.put_fact(pid, "뼈대", [])
                self.assertEqual(tutor.prepare(pid).status, 200)
                plan = tutor.store.load(pid).plan
                self.assertEqual(plan.strategy, "rule_cut")
                self.assertEqual("\n".join(b.reference for b in plan.blocks), CODE)  # 블록을 이으면 가이드 코드다
                self.assertEqual([b.kind for b in plan.blocks], ["var_during", "loop", "var_during"])  # 반복 몸통을 한 단계 더 잘랐다
            self.assertIn("count = {}", fakes.prompt(fake, "plan.hints"))  # 이름·목표는 코드 구간을 보고 한 번에 받는다
            self.assertEqual([b.name for b in tutor.store.load("p2").plan.blocks], ["이름1", "이름2", "이름3"])
            self.assertEqual([b.name for b in tutor.store.load("p3").plan.blocks], ["값 준비", "반복", "값 준비"])  # 받지 못하면 일반 문구
        finally:
            tutor.close()

    def test_small_span_slips_are_mended_by_rule(self):
        """모델이 낸 줄 구간의 작은 어긋남(한 줄 빈틈·겹침, 맨 끝 닫는 괄호 빠뜨림)은 다시 묻지 않고 고친다."""
        from ..plan.nodes import cut_by_lines

        blocks = fakes.hinted()
        slipped = [replace(b, lines=span) for b, span in zip(blocks, ([1, 2], [4, 4]))]
        self.assertEqual([b.lines for b in cut_by_lines(slipped, CODE)], [[1, 2], [3, 4]])  # 빠진 반복 머리는 뒤 블록으로
        overlap = [replace(b, lines=span) for b, span in zip(blocks, ([1, 3], [3, 4]))]
        self.assertEqual([b.lines for b in cut_by_lines(overlap, CODE)], [[1, 3], [4, 4]])
        java = "class Solution {\n    int solution(int n) {\n        int a = n;\n        return a;\n    }\n}"
        short = [replace(b, lines=span) for b, span in zip(blocks, ([1, 3], [4, 5]))]
        self.assertEqual(cut_by_lines(short, java, "java")[-1].reference, "        return a;\n    }\n}")
        self.assertIsNone(cut_by_lines([replace(b, lines=span) for b, span in zip(blocks, ([1, 1], [4, 4]))], CODE))

    def test_broken_hints_are_asked_again_once(self):
        """원칙을 어긴 질문은 그 블록만 한 번 다시 받는다. 다시 받은 것도 어기면 비워 둔다(대화 때 모델이 질문을 만든다)."""
        one, second = fakes.hinted()
        bad = fakes.drafted([{**fakes.as_dict(b), "reference": "", "lines": span} for b, span in zip((replace(one, hints=["좋아요! 무엇을 기록할까요?", *fakes.HINTS1[1:]]), second), ([1, 2], [3, 4]))])
        tutor, fake = self.tutor({"plan.solve": [SOLVED, SOLVED], "plan.draft_blocks": [bad, bad], "plan.hints": [{"blocks": [{"id": one.id, "hints": fakes.HINTS1}, {"id": second.id, "hints": ["엉뚱한 블록"]}]}]})
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks", "plan.hints"])
            self.assertIn("금지 표현", fakes.prompt(fake, "plan.hints"))
            self.assertEqual([b.hints for b in tutor.store.load("p1").plan.blocks], [fakes.HINTS1, fakes.HINTS2])  # 어기지 않은 블록은 건드리지 않는다
            tutor.store.put_problem("p2", "python", fakes.PROBLEM)
            tutor.store.put_fact("p2", "뼈대", [])
            self.assertEqual(tutor.prepare("p2").status, 200)  # 다시 받기에 실패해도(가짜 모델에 답이 없다) 계획은 만든다
            self.assertEqual([b.hints for b in tutor.store.load("p2").plan.blocks], [[], fakes.HINTS2])
        finally:
            tutor.close()

    def test_given_code_becomes_the_guide_without_solving_again(self):
        """정답 코드가 정해진 문제(기본 문제)는 새로 풀지 않는다: 그 코드가 가이드 코드가 되고, 단서·방향·단계만 모델이 쓴다. 다 정해져 있으면 모델을 부르지 않는다."""
        described = {"clues": ["'같은 이름' → 개수가 필요하다"], "approach": "이름별로 센다", "steps": ["센다", "뺀다"], "code": ""}
        tutor, fake = self.tutor({"plan.solve": [described], "plan.draft_blocks": LINED["plan.draft_blocks"] * 2})
        tutor.given = lambda pid, language: {"code": CODE + "\n"} if pid == "p1" else {"code": CODE, "clues": ["단서"], "approach": "방향", "steps": ["하나"]}
        tutor.check = lambda _pid, code: {"status": "passed" if code == CODE else "failed", "cases": []}
        try:
            self.assertEqual(tutor.prepare("p1").status, 200)
            self.assertIn("정답 코드는 아래로 정해져 있다", fakes.prompt(fake, "plan.solve"))
            guide = tutor.store.load("p1").solution
            self.assertEqual((guide.code, guide.verified, guide.approach, guide.clues), (CODE, True, "이름별로 센다", ["'같은 이름' → 개수가 필요하다"]))
            tutor.store.put_problem("p2", "java", fakes.PROBLEM)
            tutor.store.put_fact("p2", "뼈대", [])
            self.assertEqual(tutor.prepare("p2").status, 200)
            self.assertEqual(fakes.tasks(fake), ["plan.solve", "plan.draft_blocks", "plan.draft_blocks"])  # 둘째 문제는 가이드를 쓰는 호출이 없다
            self.assertEqual((tutor.store.load("p2").solution.approach, tutor.store.load("p2").solution.steps), ("방향", ["하나"]))
        finally:
            tutor.close()

    def test_canonical_replan_reuses_the_saved_guide(self):
        """정석 풀이는 문제마다 하나면 된다. 사용자 코드의 방향이 틀려 정석으로 다시 짤 때 가이드를 다시 만들지 않는다."""
        tutor, fake = self.tutor({"plan.solve": [SOLVED], "plan.draft_blocks": LINED["plan.draft_blocks"] * 2, "plan.assess": ["[check]20 N"]})
        try:
            tutor.prepare("p1")
            tutor.store.update_code("p1", "def solution(a, b):\n    return a[0]")
            fake.calls.clear()
            tutor.turn("p1", "chair", "start")
            self.assertEqual(fakes.tasks(fake), ["plan.assess", "plan.draft_blocks"])
            self.assertEqual(tutor.store.load("p1").plan.strategy, "canonical")
        finally:
            tutor.close()

    def test_two_connections_open_a_new_database_together(self):
        """화면은 첫 요청 여럿을 스레드로 동시에 받는다. 새 파일을 둘이 같이 열어도 버전 옮기기는 한 번만 돈다."""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        from ..store import Store

        for round_ in range(5):
            path, gate = str(Path(self.dir.name) / f"fresh{round_}.db"), threading.Barrier(4)

            def open_one(_):
                gate.wait()
                store = Store(path)
                try:
                    return store.conn.execute("PRAGMA user_version").fetchone()[0]
                finally:
                    store.close()

            with ThreadPoolExecutor(max_workers=4) as pool:
                self.assertEqual(list(pool.map(open_one, range(4))), [11] * 4)

    def test_old_database_migrates(self):
        conn = sqlite3.connect(self.path)
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA user_version=1")
        conn.execute("INSERT INTO problem(id, language, body) VALUES('p1', 'python', '문제')")
        conn.execute("INSERT INTO message(problem_id, mode, thread, role, text, at) VALUES('p1','chair','main','service','옛 말?','t')")
        conn.execute("INSERT INTO block_state(problem_id, block_id, code, code_hash, verdict, at) VALUES('p1','b1','x = 1','h','Y','t')")
        conn.commit()
        conn.close()
        tutor = Tutor(self.path, client=FakeLlm({}))
        try:
            self.assertEqual(tutor.store.conn.execute("PRAGMA user_version").fetchone()[0], 11)
            # 버전 8: 판정 '?'(확인 전)를 담는다. 옛 블록 상태는 그대로 옮겨진다(짝은 기본값)
            self.assertEqual([tuple(row) for row in tutor.store.conn.execute("SELECT code, verdict, renames_json FROM block_state")], [("x = 1", "Y", "[]")])
            tutor.store.conn.execute("UPDATE block_state SET verdict='?'")
            self.assertIsNone(tutor.store.load("p1").chair[0].move)
            # 버전 6: 제출에 언어·결과 종류가 붙고(옛 제출은 기본값), 문제별 학습 기록을 둔다
            tutor.store.add_submission("p1", "코드", False, language="java", status="timeout", detail={"accuracy": [3, 5]})
            tutor.store.add_submission("p1", "코드2", True)
            self.assertEqual([(row["language"], row["status"], row["detail"]) for row in tutor.store.submissions()],
                             [("java", "timeout", {"accuracy": [3, 5]}), ("python", "passed", {})])
            # 버전 10: 대화가 있던 문항은 학습 기록 행이 생기고, 가장 이른 대화 시각이 도움을 처음 쓴 시각이 된다
            none = {"solution_at": None, "solution_before_pass": False, "reset_at": None, "hints_at_reset": 0}
            self.assertEqual(tutor.store.study("p1"), {"hints_seen": 0, **none, "help_first_at": "t", "help_after_reset_at": "t"})
            tutor.store.set_study("p1", hints_seen=2)
            tutor.store.set_study("p1", solution_at="t", solution_before_pass=True)
            self.assertEqual(tutor.store.study("p1"), {"hints_seen": 2, **none, "solution_at": "t", "solution_before_pass": True, "help_first_at": "t", "help_after_reset_at": "t"})
            tutor.store.set_language("p1", "java")
            self.assertEqual(tutor.store.load("p1").language, "java")
        finally:
            tutor.close()

    def test_help_times_backfill_and_marks(self):
        """버전 10: 도움을 처음 쓴 시각. 옛 행은 남은 기록으로 채운다(힌트는 시각이 없어 가장 이른 시각, 해설·대화는 더 이른 것).
        도움 표시는 비어 있을 때만 적고, '처음부터'는 그 뒤의 도움을 다시 센다."""
        from ..store.schema import MIGRATIONS

        conn = sqlite3.connect(self.path)
        for script in MIGRATIONS[:9]:
            for statement in script.split(";"):
                if statement.strip():
                    conn.execute(statement)
        conn.execute("PRAGMA user_version=9")
        conn.execute("INSERT INTO problem(id, language, body) VALUES('p1', 'python', '문제')")
        conn.execute("INSERT INTO problem(id, language, body) VALUES('p2', 'python', '문제')")
        conn.execute("INSERT INTO problem(id, language, body) VALUES('p3', 'python', '문제')")
        conn.execute("INSERT INTO study(problem_id, hints_seen) VALUES('p1', 3)")
        conn.execute("INSERT INTO study(problem_id, solution_at) VALUES('p2', '2001-01-01T00:00:09+09:00')")
        conn.execute("INSERT INTO message(problem_id, mode, thread, role, text, at) VALUES('p2','chair','main','user','질문','2001-01-01T00:00:05+09:00')")
        conn.execute("INSERT INTO study(problem_id) VALUES('p3')")
        conn.commit()
        conn.close()
        tutor = Tutor(self.path, client=FakeLlm({}))
        try:
            first = {pid: tutor.store.study(pid)["help_first_at"] for pid in ("p1", "p2", "p3")}
            self.assertEqual(first, {"p1": "0001-01-01T00:00:00+00:00", "p2": "2001-01-01T00:00:05+09:00", "p3": None})
            from ..store import sqlite as stored

            with mock.patch.object(stored, "now", return_value="A"):
                tutor.store.mark_help("p3")
            with mock.patch.object(stored, "now", return_value="B"):
                tutor.store.mark_help("p3")
                tutor.store.mark_reset("p3")
            study = tutor.store.study("p3")
            self.assertEqual((study["help_first_at"], study["help_after_reset_at"], study["reset_at"]), ("A", None, "B"))
            tutor.store.set_study("p3", hints_seen=2)
            tutor.store.mark_reset("p3")  # 본 힌트 수는 누적으로 남고, 이번 풀이는 그 수부터 센다
            self.assertEqual((tutor.store.study("p3")["hints_seen"], tutor.store.study("p3")["hints_at_reset"]), (2, 2))
            tutor.store.set_study("p3", hints_seen=3)
            self.assertEqual(tutor.store.load("p3").hints_seen, 1)  # 피드백이 읽는 본 힌트 수는 이번 풀이 것
            tutor.store.set_study("p3", help_first_at=None, help_after_reset_at=None)
            tutor.store.mark_help("p3", this_try_only=True)  # 이번 풀이에만 도움(첫 풀이의 판정은 그대로)
            self.assertEqual((tutor.store.study("p3")["help_first_at"], bool(tutor.store.study("p3")["help_after_reset_at"])), (None, True))
        finally:
            tutor.close()

    # 학습자 정보(약점·눈높이)가 의자·가이드 대화에 들어간다
    WEAK = "이 학습자가 다른 문제에서 되풀이한 실수: 콜론(:) 빠짐(2번), 들여쓰기 어긋남(1번)."
    BEGINNER = "학습자는 입문 단계다."
    ADVANCED = "학습자는 익숙한 단계다."

    def passed(self, store, count: int, start: int = 0, first_ok: bool = True) -> None:
        for n in range(start, start + count):
            store.put_problem(f"q{n}", "python", "문제")
            if not first_ok:
                store.add_submission(f"q{n}", "코드", False)
            store.add_submission(f"q{n}", "코드", True)

    def test_learner_level_from_submissions(self):
        tutor, _ = self.tutor({})
        store = tutor.store
        try:
            self.assertEqual((store.learner_level(), store.load("p1").level), ("beginner", "beginner"))  # 제출이 없으면 입문
            self.passed(store, 4)
            store.put_problem("q4", "python", "문제")
            store.add_submission("q4", "코드", True, status="toolchain_missing")  # 도구가 없어 못 돌린 제출은 세지 않는다
            self.assertEqual(store.learner_level(), "beginner")
            store.add_submission("q4", "코드", True)
            self.assertEqual(store.learner_level(), "middle")
            self.passed(store, 20, start=5, first_ok=False)  # 25문항 통과, 첫 제출 통과 5/25
            self.assertEqual(store.learner_level(), "middle")
        finally:
            tutor.close()
        other = Tutor(str(Path(self.dir.name) / "other.db"), client=FakeLlm({}))
        try:
            for n in range(25):  # 첫 제출이 toolchain_missing이면 그다음 제출이 첫 제출이다
                other.store.put_problem(f"q{n}", "python", "문제")
                other.store.add_submission(f"q{n}", "코드", False, status="toolchain_missing")
                other.store.add_submission(f"q{n}", "코드", True)
            self.assertEqual(other.store.learner_level(), "advanced")
            self.passed(other.store, 26, start=25, first_ok=False)  # 첫 제출 통과 25/51 < 0.5
            self.assertEqual(other.store.learner_level(), "middle")
        finally:
            other.close()

    def talk(self, tutor, fake) -> tuple[str, str, str]:
        """의자 시작(저장 질문) → 내용 있는 말(chair.ask) → 가이드에서 내용 있는 말(guide.lead). (의자 프롬프트, 가이드 프롬프트, 의자 말)
        블록을 여는 말과 '모르겠어요' 뒤는 저장 힌트라 모델을 부르지 않는다."""
        tutor.turn("p1", "chair", "start")
        reply = tutor.turn("p1", "chair", "message", text="이름을 세요").body["messages"][-1]["text"]
        tutor.turn("p1", "guide", "message", text="이름을 세요")
        for call in fake.calls:  # 학습자 구역은 캐시되는 앞부분 뒤에 있다
            content = call["messages"][-1]["content"]
            if call["task"] in ("chair.ask", "guide.lead") and "학습자:" in content:
                self.assertGreater(content.index("학습자:"), call["messages"][-1]["cache_prefix"])
        return fakes.prompt(fake, "chair.ask"), fakes.prompt(fake, "guide.lead"), reply

    TALK = {"chair.judge": ["[check]N"], "chair.ask": ["그렇죠, 같은 이름이 두 번 나오면 어떻게 될까요?"], "guide.judge": ["[check]N"],
            "guide.lead": ["이 빈칸에는 무엇을 담을까요?"]}

    def seed_pitfalls(self, store) -> None:
        store.put_problem("p0", "python", "다른 문제")
        rows = [("p0", "missing_colon", "h1"), ("p0", "missing_colon", "h2"), ("p0", "indent", "h3")]
        store.conn.executemany("INSERT INTO pitfall_hit(problem_id, pitfall, code_hash, at) VALUES(?, ?, ?, 't')", rows)
        store.conn.commit()

    def test_pitfalls_and_beginner_reach_chair_and_guide(self):
        tutor, fake = self.tutor({**DRAFT, **self.TALK})
        try:
            self.seed_pitfalls(tutor.store)
            chair, guide, reply = self.talk(tutor, fake)
            for prompt in (chair, guide):
                for must in (self.WEAK, "지금 블록이 이 실수와 닿을 때만", "실수의 이름을 그대로 말하지 않는다", self.BEGINNER, "한 번에 한 가지만 묻는다"):
                    self.assertIn(must, prompt)
                self.assertNotIn(self.ADVANCED, prompt)
            self.assertEqual(reply, FALLBACK["clue"])  # 동의로 시작한 말은 다시 부르지 않고 대체 질문
        finally:
            tutor.close()

    def test_advanced_and_plain_learner(self):
        tutor, fake = self.tutor({**DRAFT, **self.TALK})
        try:
            self.passed(tutor.store, 25)
            chair, guide, _ = self.talk(tutor, fake)
            for prompt in (chair, guide):
                self.assertIn(self.ADVANCED + " 기본 설명을 줄이고, 경계 입력과 시간 복잡도를 겨누는 질문을 먼저 고른다.", prompt)
                self.assertNotIn("되풀이한 실수", prompt)
        finally:
            tutor.close()
        Path(self.path).unlink()
        tutor, fake = self.tutor({**DRAFT, **self.TALK})
        try:
            self.passed(tutor.store, 5)  # 중간이고 함정이 없으면 구역이 없다(프롬프트가 예전과 같다)
            chair, guide, _ = self.talk(tutor, fake)
            for prompt in (chair, guide):
                self.assertNotIn("학습자", prompt)
        finally:
            tutor.close()

    def test_learner_info_with_adopted_plan(self):
        """기본 문제처럼 미리 만든 계획을 넣고 시작해도 대화에 학습자 정보가 들어간다."""
        tutor, fake = self.tutor(self.TALK)
        try:
            self.seed_pitfalls(tutor.store)
            ready = {"fact": {"spec": "뼈대", "patterns": [], "skills": [], "size": 0},
                     "solution": {"approach": "이름별로 센다", "steps": ["센다"], "code": CODE, "verified": True},
                     "plan": json.loads(plan_to_json(fakes.planned(fakes.hinted())))}
            self.assertTrue(tutor.adopt("p1", ready))
            chair, guide, _ = self.talk(tutor, fake)
            self.assertNotIn("plan.draft_blocks", fakes.tasks(fake))  # 블록 설계를 거치지 않는다
            for prompt in (chair, guide):
                self.assertIn(self.WEAK, prompt)
                self.assertIn(self.BEGINNER, prompt)
        finally:
            tutor.close()


class PitfallGroupTest(unittest.TestCase):
    def test_overlapping_pitfalls_are_counted_together(self):
        """같은 경계 실수가 off_by_one과 wrong_compare로 갈려 각 1번으로만 남았다. 셀 때만 한 묶음으로 센다(저장 id는 그대로)."""
        with tempfile.TemporaryDirectory() as folder:
            tutor = Tutor(str(Path(folder) / "t.db"))
            try:
                for pid, pitfall, at in (("p1", "off_by_one", "2026-11-01"), ("p2", "wrong_compare", "2026-11-02"), ("p3", "wrong_init", "2026-11-03")):
                    tutor.store.put_problem(pid, "python", fakes.PROBLEM)
                    with tutor.store.conn:
                        tutor.store.conn.execute("INSERT INTO pitfall_hit(problem_id, pitfall, code_hash, at) VALUES(?, ?, 'h', ?)", (pid, pitfall, at))
                self.assertEqual(tutor.store._frequent_pitfalls(), [("off_by_one", 2), ("wrong_init", 1)])
                stored = [row[0] for row in tutor.store.conn.execute("SELECT pitfall FROM pitfall_hit ORDER BY at")]
                self.assertEqual(stored, ["off_by_one", "wrong_compare", "wrong_init"])
            finally:
                tutor.close()
