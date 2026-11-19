"""튜터 말의 칸 저장: message.parts_json 열, 저장하는 줄의 parts, 응답의 parts. 가짜 모델만 쓴다.

계약
- 마지막 스키마 버전이 message.parts_json(TEXT, NULL 허용)을 더한다. 옛 기록은 NULL이다.
- parts는 서비스 말(튜터 대화 줄)에만 있다. 꼴: {"block_index": int, "result"?: str, "question"?: str, "note"?: str, "buttons"?: [str]}.
  비어 있는 칸은 키를 두지 않는다. 길 안내 글(막혔을 때 갈 길)은 칸 글이 아니라 buttons 표시로만 남고, text에는 지금처럼 그대로 들어간다.
- 저장 줄(save.nodes.collect의 messages)은 "parts" 키를 늘 가진다(없으면 None).
- 응답의 메시지(respond.messages_body)는 parts가 있는 말에만 "parts" 키를 낸다. 없는 말은 키가 없어 응답 모양이 이전과 같다.
- text는 지금과 같은 줄 꼴로 채운다. 모델 호출 수는 바뀌지 않는다.
"""

import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from . import fakes
from . import test_advance_rule as ar
from .test_tutor import DRAFT
from ..common.talk_rules import ANSWER_LEAD, BACK_LEAD, EXAMPLES_ONLY, OWN_WAY, RETRY_LEAD, SKIPPED, UNRUN_NO, WITHDRAWN, rename_note
from ..turn.code_check import code_hash
from ..turn.moves import FOUND_OK, HINTS_DONE
from ..state import BlockState
from .test_pipeline import SORT_BLOCKS, exec_check, sort_check
from ..llm import FakeLlm
from ..main import Tutor
from ..save.nodes import collect
from ..save.respond import shown_count
from ..store.schema import MIGRATIONS

KEYS = {"block_index", "result", "question", "note", "buttons"}
OLD_VERSION = 11  # 칸 열을 더하기 전의 마지막 버전
NOTE = "제목이 같은 책을 한 묶음으로 보셨어요."
ASKED = "`groups[3]`의 값은 얼마인가요?"


def parts_of(rows):
    """저장 줄 가운데 마지막 서비스 말의 parts."""
    return [r for r in rows if r["role"] == "service"][-1]["parts"]


def strings(parts):
    return [parts[k] for k in ("result", "question", "note") if k in parts] + list(parts.get("buttons", []))


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.dir.name) / "tutor.db")

    def tearDown(self):
        self.dir.cleanup()

    def old_db(self):
        conn = sqlite3.connect(self.path)
        for script in MIGRATIONS[:OLD_VERSION]:
            for statement in script.split(";"):
                if statement.strip():
                    conn.execute(statement)
        conn.execute(f"PRAGMA user_version={OLD_VERSION}")
        conn.execute("INSERT INTO problem(id, language, body) VALUES('p1', 'python', '문제')")
        conn.execute("INSERT INTO message(problem_id, mode, thread, block_index, role, text, at, move) VALUES('p1','chair','main',0,'service','옛 말?\n옛 근거','t','open')")
        conn.execute("INSERT INTO message(problem_id, mode, thread, block_index, role, text, at) VALUES('p1','chair','main',0,'user','옛 답','t2')")
        conn.commit()
        conn.close()

    def test_old_database_gets_parts_column_and_old_rows_read_as_before(self):
        self.assertGreater(len(MIGRATIONS), OLD_VERSION)  # 이 PR이 마이그레이션을 더한다
        self.old_db()
        tutor = Tutor(self.path, client=FakeLlm({}))
        try:
            conn = tutor.store.conn
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], len(MIGRATIONS))
            self.assertIn("parts_json", [row["name"] for row in conn.execute("PRAGMA table_info(message)")])
            self.assertEqual([tuple(r) for r in conn.execute("SELECT text, parts_json FROM message ORDER BY id")], [("옛 말?\n옛 근거", None), ("옛 답", None)])
            got = tutor.session("p1", "chair").body["chair"]
            self.assertEqual([(m["role"], m["text"], m["move"], m["block_index"]) for m in got], [("service", "옛 말?\n옛 근거", "open", 0), ("user", "옛 답", None, 0)])
            self.assertTrue(all("parts" not in m for m in got))  # 옛 말은 응답 모양이 그대로다
        finally:
            tutor.close()

    def test_reopening_is_safe_and_keeps_data(self):
        self.old_db()
        for _ in range(3):
            tutor = Tutor(self.path, client=FakeLlm({}))
            try:
                self.assertEqual(tutor.store.conn.execute("PRAGMA user_version").fetchone()[0], len(MIGRATIONS))
                self.assertEqual(tutor.store.message_count("p1"), 2)
            finally:
                tutor.close()


class SavedPartsTest(unittest.TestCase):
    """저장하는 줄(collect)의 parts. 상황은 블록 진행 시험의 틀을 쓴다."""

    def saved(self, mode, i, make, event_chat=None):
        ctx = ar.context(mode, i, event_chat)
        state, scripts, check = make(mode, i, ctx)
        done, fake = fakes.go(state, scripts, check)
        self.assertIsNone(done.get("error"))
        rows = collect(done)["changes"]["messages"]
        return done, fake, rows, ar.saved(done, mode)[0]

    def check_common(self, mode, done, rows, ctx_after):
        """모든 상황에 같은 것: 사용자 줄에는 parts가 없고, 키가 정해진 것뿐이며, 의자에서는 '할 것'과 잠긴 이름이 새지 않는다."""
        for row in rows:
            self.assertIn("parts", row)
            self.assertEqual(row["parts"] is None, row["role"] == "user")
        parts = parts_of(rows)
        self.assertLessEqual(set(parts), KEYS)
        self.assertEqual(parts["block_index"], rows[-1]["block_index"])
        for value in strings(parts):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())
        blob = json.dumps(parts, ensure_ascii=False)
        if mode == "chair":
            self.assertNotIn("목표-", blob)  # 의자에서 찾기 전 블록의 '할 것'은 칸에도 없다
            for later in ar.BLOCKS[shown_count(ctx_after, "chair"):]:
                self.assertNotIn(later.name, blob)
        self.assertNotIn(ANSWER_LEAD.strip(), blob)  # 길 안내 글은 칸이 아니라 단추 표시다
        return parts

    def in_text(self, text, parts):
        """칸 글이 text 안에 결과 → 질문 → 근거 차례로 그대로 들어 있다."""
        last = -1
        for key in ("result", "question", "note"):
            if key in parts:
                at = text.find(parts[key])
                self.assertGreater(at, last, (key, parts, text))
                last = at

    def test_opening_next_block_stores_question_only(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                for i in (0, 1):
                    done, fake, rows, after = self.saved(mode, i, ar.code(ar.PASS))
                    parts = self.check_common(mode, done, rows, after)
                    self.assertEqual(len(fake.calls), 0)  # 모델 호출 수 그대로
                    self.assertEqual(parts["block_index"], i + 1)
                    self.assertEqual(parts["question"], ar.HINTS[i + 1][0])  # 다음 블록의 저장 힌트
                    self.assertNotIn("buttons", parts)
                    self.in_text(rows[-1]["text"], parts)
                    self.assertTrue(rows[-1]["text"].endswith(ar.HINTS[i + 1][0]))

    def test_message_N_stores_question_and_note(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                make = ar.talk("한 번씩 다 더하면 될 것 같아요", "[check]N1", {"note": NOTE, "question": ASKED})
                done, fake, rows, after = self.saved(mode, 0, make)
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual((parts["question"], parts["note"], parts["block_index"]), (ASKED, NOTE, 0))
                self.assertNotIn("result", parts)
                self.assertEqual(rows[-1]["text"], ASKED + "\n" + NOTE)  # text는 지금 줄 꼴 그대로(질문 다음 근거)
                self.assertEqual(len(fake.calls), 2)  # 판정 1 + 말 1

    def test_message_N_without_note_has_no_note_key(self):
        done, fake, rows, after = self.saved("chair", 0, ar.talk("한 번씩 다 더하면 될 것 같아요", "[check]N1", ar.ASKED))
        parts = self.check_common("chair", done, rows, after)
        self.assertEqual(parts["question"], ar.ASKED)
        self.assertNotIn("note", parts)
        self.assertEqual(rows[-1]["text"], ar.ASKED)

    def test_do_not_know_stores_next_saved_hint(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.talk("모르겠어요"))
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual(parts["question"], ar.HINTS[0][1])
                self.assertNotIn("result", parts)
                self.assertEqual(len(fake.calls), 0)

    def test_ask_for_answer_marks_a_button_instead_of_a_way_text(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.talk("그냥 답 코드 알려 줘"))
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual(parts["question"], ar.HINTS[0][1])
                self.assertTrue(parts["buttons"])  # 이 블록 코드 받기 같은 단추 표시
                self.assertEqual(rows[-1]["text"], ar.HINTS[0][1] + "\n" + ANSWER_LEAD.strip())  # text는 그대로
                self.assertEqual(len(fake.calls), 0)

    def test_ask_for_answer_keeps_the_no_answer_sentence_in_result_and_the_way_as_button(self):
        sentence = ANSWER_LEAD.split(".")[0] + "."  # 답을 주지 않는다는 문장
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.talk("그냥 답 코드 알려 줘"))
                parts = self.check_common(mode, done, rows, after)
                self.assertIn("result", parts)
                self.assertIn(sentence, parts["result"])  # 첫 문장은 결과 칸에 남는다
                self.assertNotIn("이 블록 채우기", parts["result"])  # 길 안내는 글이 아니라 단추다
                self.assertIn("fill", parts["buttons"])
                self.assertEqual(parts["question"], ar.HINTS[0][1])
                self.assertEqual(len(fake.calls), 0)

    def test_other_way_leads_stay_buttons_only(self):
        from ..common.talk_rules import FILL_TIP

        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                chat = [fakes.service(ar.HINTS[0][0], 0, "m1", ar.OPENING[mode]), fakes.user("모르겠어요", 0, "u1"), fakes.service(ar.HINTS[0][1], 0, "m2", "clue")]
                done, fake, rows, after = self.saved(mode, 0, ar.talk("잘 모르겠음"), chat)
                parts = self.check_common(mode, done, rows, after)
                self.assertIn(FILL_TIP.strip(), rows[-1]["text"])  # 길 안내가 붙은 말이다(전제)
                self.assertNotIn("result", parts)  # 결과 칸에 길 안내 문장이 새로 생기지 않는다
                self.assertIn("fill", parts["buttons"])
                self.assertEqual(parts["question"], ar.HINTS[0][2])
                self.assertEqual(len(fake.calls), 0)

    def test_ask_for_answer_after_all_hints_keeps_both_sentences_on_screen(self):
        """힌트를 다 본 뒤 답을 달라고 하면 고정 말(HINTS_DONE)과 답을 주지 않는다는 문장만 남는다.
        칸 글 없이 단추만 두어 화면이 글 전체를 결과로 보인다(결과 칸에 거절만 넣으면 '힌트는 다 봤어요'가 빠진다)."""
        from ..common.talk_rules import ANSWER_NO

        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                chat = [fakes.service(ar.HINTS[0][0], 0, "m1", ar.OPENING[mode]), fakes.user("모르겠어요", 0, "u1"), fakes.service(ar.HINTS[0][1], 0, "m2", "clue"),
                        fakes.user("몰라요", 0, "u2"), fakes.service(ar.HINTS[0][2], 0, "m3", "trace")]
                done, fake, rows, after = self.saved(mode, 0, ar.talk("그냥 답 코드 알려 줘"), chat)
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual(rows[-1]["text"], HINTS_DONE + "\n" + ANSWER_NO)
                self.assertEqual(parts, {"block_index": 0, "buttons": ["fill"]})
                self.assertEqual(len(fake.calls), 0)

    def test_failed_check_stores_result_then_question(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.code(ar.FAIL))
                parts = self.check_common(mode, done, rows, after)
                self.assertTrue(parts["result"].startswith(RETRY_LEAD.strip()))
                self.assertEqual(parts["question"], ar.HINTS[0][1])
                self.in_text(rows[-1]["text"], parts)
                self.assertTrue(rows[-1]["text"].startswith(RETRY_LEAD) and rows[-1]["text"].endswith(ar.HINTS[0][1]))
                self.assertEqual(len(fake.calls), 0)

    def test_passed_check_opens_next_block_with_its_head_number(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.code(ar.PASS))
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual((parts["block_index"], parts["question"]), (1, ar.HINTS[1][0]))
                self.assertEqual(len(fake.calls), 0)

    def test_skip_stores_result_then_next_question(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                done, fake, rows, after = self.saved(mode, 0, ar.code(ar.FAIL, ar.never, quiet=True, skip=True))
                parts = self.check_common(mode, done, rows, after)
                self.assertEqual(parts["result"], SKIPPED.strip())
                self.assertEqual((parts["block_index"], parts["question"]), (1, ar.HINTS[1][0]))
                self.in_text(rows[-1]["text"], parts)
                self.assertEqual(len(fake.calls), 0)

    def test_last_block_pass_in_guide_has_no_question(self):
        done, fake, rows, after = self.saved("guide", ar.N - 1, ar.code(ar.PASS))
        parts = self.check_common("guide", done, rows, after)
        self.assertNotIn("question", parts)
        self.assertTrue(parts.get("result") or parts.get("buttons"))
        self.assertEqual(len(fake.calls), 0)

    def test_text_stays_the_line_form_of_the_reply(self):
        """칸을 더해도 reply(곧 text)는 그대로다. 줄 수 세기·보고서·평가기가 읽는 것이 text다."""
        for make in (ar.talk("모르겠어요"), ar.talk("그냥 답 코드 알려 줘"), ar.code(ar.FAIL), ar.code(ar.PASS)):
            done, _, rows, _ = self.saved("chair", 0, make)
            self.assertEqual(rows[-1]["text"], done["result"]["reply"])


class StoredAndServedTest(unittest.TestCase):
    """SQLite 파일과 응답까지(진짜 저장소 + 가짜 모델)."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.dir.name) / "tutor.db")

    def tearDown(self):
        self.dir.cleanup()

    def tutor(self, scripts):
        tutor = Tutor(self.path, client=FakeLlm(fakes.spoken({**DRAFT, **scripts})))
        tutor.store.put_problem("p1", "python", fakes.PROBLEM, title="추천 서가에 꽂히는 책")
        tutor.store.put_fact("p1", "문자열 배열 둘, 남는 원소 하나", [])
        return tutor

    def test_parts_are_stored_and_served_and_old_shape_is_kept(self):
        tutor = self.tutor({"chair.judge": ["[check]N1"], "chair.ask": [{"note": NOTE, "question": ASKED}]})
        try:
            start = tutor.turn("p1", "chair", "start")
            first = start.body["messages"][-1]
            self.assertEqual((first["text"], first["parts"]), (fakes.HINTS1[0], {"block_index": 0, "question": fakes.HINTS1[0]}))
            self.assertEqual(set(first) - {"parts"}, {"id", "role", "text", "at", "block_index", "move"})  # 다른 키는 그대로
            said = tutor.turn("p1", "chair", "message", text="한 번씩만 세면 될 것 같아요")
            user, service = said.body["messages"][-2:]
            self.assertNotIn("parts", user)  # 사용자 말에는 칸이 없다
            self.assertEqual(service["parts"], {"block_index": 0, "question": ASKED, "note": NOTE})
            self.assertEqual(service["text"], ASKED + "\n" + NOTE)
            rows = tutor.store.conn.execute("SELECT role, parts_json FROM message ORDER BY id").fetchall()
            self.assertEqual([(r["role"], json.loads(r["parts_json"]) if r["parts_json"] else None) for r in rows],
                             [("service", first["parts"]), ("user", None), ("service", service["parts"])])
            self.assertEqual(tutor.session("p1", "chair").body["chair"][-1]["parts"], service["parts"])  # 다시 열어도 같다
            self.assertNotIn("목표-", json.dumps(said.body, ensure_ascii=False))  # 의자 응답에 '할 것'이 없다
        finally:
            tutor.close()

    def test_old_and_new_messages_mix(self):
        tutor = self.tutor({})
        try:
            tutor.store.conn.execute("INSERT INTO message(problem_id, mode, thread, block_index, role, text, at, move) VALUES('p1','chair','main',0,'service','옛 말?','t','open')")
            tutor.store.conn.commit()
            body = tutor.session("p1", "chair").body
            self.assertEqual([m["text"] for m in body["chair"]], ["옛 말?"])
            self.assertNotIn("parts", body["chair"][0])
        finally:
            tutor.close()

    def test_reread_failure_path_keeps_parts(self):
        """저장 뒤 다시 읽기가 실패하면 저장할 줄을 문맥에 얹어 응답한다(_merged). 그 응답도 같은 parts를 낸다."""
        tutor = self.tutor({})
        try:
            real_load, calls = tutor.store.load, {"n": 0}

            def load_once(problem_id):
                calls["n"] += 1
                if calls["n"] > 1:
                    raise sqlite3.OperationalError("reread")
                return real_load(problem_id)

            with mock.patch.object(tutor.store, "load", side_effect=load_once):
                ok = tutor.turn("p1", "chair", "start")
            self.assertEqual(ok.status, 200)
            last = ok.body["messages"][-1]
            self.assertEqual((last["text"], last["parts"]), (fakes.HINTS1[0], {"block_index": 0, "question": fakes.HINTS1[0]}))
            self.assertEqual(tutor.session("p1", "chair").body["chair"][-1]["parts"], last["parts"])  # 저장된 것과 같다
        finally:
            tutor.close()

    def test_reread_failure_path_for_a_row_without_parts(self):
        """다시 읽기 실패 + parts 없는 줄(사용자 말·꼬리질문 등): 키 없이 지금 모양 그대로."""
        from ..save.nodes import _merged

        ctx = fakes.context(plan=fakes.planned(fakes.hinted()), open_count=1)
        state = fakes.make_state("turn", ctx, mode="chair", event="message", text="안녕")
        state["changes"] = {"messages": [{"mode": "chair", "thread": "main", "role": "user", "text": "안녕", "block_index": 0, "quote_id": None, "move": None, "at": "t"},
                                         {"mode": "chair", "thread": "main", "role": "service", "text": "옛 꼴?", "block_index": 0, "quote_id": None, "move": "open", "at": "t", "parts": None}],
                            "plan": ctx.plan, "open_count": 1, "explain": None, "debug_state": None}
        merged = _merged(state)  # parts 키가 없는 줄이 와도(옛 호출) 깨지지 않는다
        self.assertEqual([m.text for m in merged.chair], ["안녕", "옛 꼴?"])
        from ..save.respond import messages_body
        self.assertTrue(all("parts" not in m for m in messages_body(merged.chair)))


class ButtonMarksTest(unittest.TestCase):
    """단추 표시와 칸에 넣지 않는 앞말(이음말). 글(text)은 그대로다."""

    def parts(self, mode, i, make, chat=None):
        done, fake = fakes.go(*make(mode, i, ar.context(mode, i, chat)))
        rows = collect(done)["changes"]["messages"]
        return parts_of(rows), rows[-1]["text"], fake

    def test_bare_lead_stays_in_text_only(self):
        parts, text, _ = self.parts("chair", 0, ar.talk("오늘 저녁 메뉴는 무엇으로 할지 고민이에요", "[check]O"))
        self.assertTrue(text.startswith(BACK_LEAD.strip()))
        self.assertEqual(parts, {"block_index": 0, "question": ar.HINTS[0][1]})

    def test_hints_done_is_a_fill_mark(self):
        S, U = fakes.service, fakes.user
        chat = [S(ar.HINTS[0][0], 0, "s0", "open"), U("모르겠어요", 0, "u0"), S(ar.HINTS[0][1], 0, "s1", "clue"), U("모르겠어요", 0, "u1"), S(ar.HINTS[0][2], 0, "s2", "trace")]
        parts, text, fake = self.parts("chair", 0, ar.talk("모르겠어요"), chat)
        self.assertEqual((parts, text, len(fake.calls)), ({"block_index": 0, "buttons": ["fill"]}, HINTS_DONE, 0))

    def test_skip_only_on_the_current_block_and_run_on_the_last(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                self.assertEqual(self.parts(mode, 1, ar.code(ar.FAIL))[0]["buttons"], ["skip"])
                self.assertNotIn("buttons", self.parts(mode, 1, ar.code(ar.FAIL, back=1))[0])  # 앞 블록을 다시 확인: 넘어가기 단추가 없다
                self.assertEqual(self.parts(mode, ar.N - 1, ar.code(ar.PASS))[0]["buttons"], ["run"])


class SituationPartsTest(unittest.TestCase):
    """확인 결과마다 결과 칸에 들어가는 줄: 오류, 실행 못 함, 앞 블록 다시 확인, 끝까지 내 방식, 물린 뒤 블록, 이름 안내, 모델이 쓰는 길."""

    def parts(self, state, scripts, check):
        done, fake = fakes.go(state, scripts, check)
        self.assertIsNone(done.get("error"))
        return parts_of(collect(done)["changes"]["messages"]), len(fake.calls)

    def ar_parts(self, mode, i, make, **extra):
        return self.parts(*make(mode, i, ar.context(mode, i, **extra)))

    def sort_turn(self, blocks, mode="guide", open_count=1, chat=None):
        ctx = fakes.context(plan=fakes.planned(blocks), open_count=open_count, **{mode: chat or [fakes.service(fakes.HINTS1[0], 0)]})
        return fakes.make_state("turn", ctx, mode=mode, event="block_filled", block_id="b1", code="arr = sorted(items)")

    def test_syntax_error_is_a_result_with_skip_and_no_question(self):
        broken = ["def solution(items):\n    total = (0", *ar.PASS[1:]]
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                parts, calls = self.ar_parts(mode, 0, ar.code(broken))
                self.assertEqual((set(parts), parts["buttons"], calls), ({"block_index", "result", "buttons"}, ["skip"], 0))
                self.assertTrue(parts["result"].startswith(RETRY_LEAD.strip()))
                self.assertIn("SyntaxError", parts["result"])

    def test_unrun_check_is_a_result_with_skip(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                parts, _ = self.ar_parts(mode, 1, ar.code(ar.PASS, ar.unrun))
                self.assertIn(UNRUN_NO, parts["result"])
                self.assertEqual(parts["buttons"], ["skip"])

    def test_earlier_block_passing_again_is_found_ok_only(self):
        for mode in ("chair", "guide"):
            for i in (1, 2):
                with self.subTest(mode=mode, i=i):
                    self.assertEqual(self.ar_parts(mode, i, ar.code(ar.PASS, back=1)), ({"block_index": i - 1, "result": FOUND_OK}, 0))

    def test_own_way_is_a_result_without_question(self):
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                parts, calls = self.ar_parts(mode, 0, ar.code(ar.FAIL, ar.never, quiet=True, skip=True, own_way=True))
                self.assertEqual((parts["result"].split("\n"), calls), ([SKIPPED.strip(), OWN_WAY.strip()], 0))
                self.assertNotIn("question", parts)

    def test_withdrawn_line_is_in_result(self):
        states = {b.id: BlockState(b.id, c, code_hash(c), "Y") for b, c in zip(ar.BLOCKS[:2], ar.PASS[:2])}
        other = ["def solution(items):\n    total = 0", *ar.PASS[1:]]
        for mode in ("chair", "guide"):
            with self.subTest(mode=mode):
                parts, _ = self.ar_parts(mode, 2, ar.code(other, back=2), block_states=states)
                self.assertEqual(parts, {"block_index": 0, "result": f"{FOUND_OK}\n{WITHDRAWN.format(n=1)}"})

    def test_rename_note_is_in_result(self):
        note = rename_note([["arr", "order"]])
        self.assertEqual(self.parts(self.sort_turn(SORT_BLOCKS), {}, sort_check([])),
                         ({"block_index": 1, "result": note, "question": fakes.HINTS2[0]}, 0))  # 저장 힌트로 다음 블록을 연다
        chair = [fakes.service(fakes.HINTS1[0], 0), fakes.service(fakes.HINTS2[0], 1, "m2")]
        self.assertEqual(self.parts(self.sort_turn(SORT_BLOCKS, "chair", 2, chair), {}, sort_check([])),
                         ({"block_index": 0, "result": f"{FOUND_OK}\n{note}"}, 0))  # 앞 블록 다시 확인(마침 말 뒤)

    def test_model_path_keeps_said_and_rename_in_result(self):
        asked = "`order`에서 무엇을 빼야 할까요?"
        blocks = [SORT_BLOCKS[0], replace(SORT_BLOCKS[1], hints=[])]  # 저장 힌트가 없어 모델이 다음 블록을 연다
        self.assertEqual(self.parts(self.sort_turn(blocks), {"guide.lead": [asked]}, sort_check([])),
                         ({"block_index": 1, "result": rename_note([["arr", "order"]]), "question": asked}, 1))
        parts = self.ar_parts("chair", ar.N - 1, ar.code(ar.PASS, exec_check([], ar.CASES[:1])))  # 공개 예시로만 돌았다(said), 정리 질문은 모델
        self.assertEqual(parts, ({"block_index": ar.N - 1, "result": EXAMPLES_ONLY, "question": ar.ASKED, "buttons": ["run"]}, 1))


if __name__ == "__main__":
    unittest.main()
