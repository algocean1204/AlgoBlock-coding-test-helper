"""A1 문항 읽기. OCR은 바꿔 끼운다(실제 tesseract 확인은 TS 문서에 기록)."""

import io
import unittest
from unittest.mock import patch

from . import fakes
from ..ingest import IngestError, extract, extract_with_note
from ..ingest import ocr as ocr_tool
from ..ingest.ocr import ocr_ok, run_ocr
from ..ingest.text import join_text
from ..llm import FakeLlm, LlmNotConfigured, LlmTimeout, use_llm

GOOD_OCR = "## 입력 첫 줄에 두 정수 a와 b가 공백으로 주어진다"
SECOND_OCR = "## 출력 두 정수 a와 b의 합을 한 줄에 출력한다"  # 앞 장과 겹치지 않는 둘째 장(겹치면 merge가 뺀다)


def text_pdf(words: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({words}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)


def blank_pdf() -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def run(text, files, scripts=None, ocr_texts=None):
    fake = FakeLlm(scripts or {})
    with use_llm(fake), patch.object(ocr_tool, "run_ocr", side_effect=list(ocr_texts or [])):
        return extract(text, files), fake


def run_note(text, files, scripts, ocr_texts=()):
    """(본문, tesseract로 읽은 장이 있는가, 가짜 모델, tesseract를 부른 장들)."""
    fake = FakeLlm(scripts)
    with use_llm(fake), patch.object(ocr_tool, "run_ocr", side_effect=list(ocr_texts)) as ocr:
        body, used = extract_with_note(text, files)
    return body, used, fake, [call.args[0] for call in ocr.call_args_list]


class TextTest(unittest.TestCase):
    def test_split_capture_overlap_is_kept_once(self):
        from ..ingest.text import drop_overlap

        top = "## 제한사항\n- n은 1 이상입니다.\n\n| 입력 | 결과 |\n|---|---|\n| [1, 2] | 3 |"
        bottom = "| 입력 | 결과 |\n| --- | --- |\n|  [1, 2] | 3 |\n| [4] | 4 |"
        self.assertEqual(drop_overlap(top, bottom), (top, "| [4] | 4 |"))  # 겹친 표 머리와 첫 줄은 한 번만
        self.assertEqual(drop_overlap("## 문제\n첫 문단", "## 입출력 예\n둘째"), ("## 문제\n첫 문단", "## 입출력 예\n둘째"))
        cut = "앞 문단\n상자는 1초에 하나씩 벨트에 오릅"  # 앞 장이 줄 가운데서 잘렸다
        self.assertEqual(drop_overlap(cut, "상자는 1초에 하나씩 벨트에 오릅니다.\n뒤 문단"), ("앞 문단", "상자는 1초에 하나씩 벨트에 오릅니다.\n뒤 문단"))
        # 글자 읽기가 겹친 줄을 장마다 조금 다르게 읽었다. 거의 같으면 같은 줄이다
        page1 = "앞 문단\n벨트에 오른 상자는 정확히 travel초 뒤에 내립니다.\n매초 먼저 그 시각에 내릴 상자가 내립니다."
        page2 = "벨트에 오른 상자는 정확히 trave1초 뒤에 내립니다.\n매초 먼저 그 시각에 내릴 상자가 내립니다,\n새 문단"
        self.assertEqual(drop_overlap(page1, page2), (page1, "새 문단"))
        self.assertEqual(drop_overlap("앞\n1 2 3", "1 2 4\n뒤"), ("앞\n1 2 3", "1 2 4\n뒤"))  # 우연히 비슷한 짧은 줄은 겹침이 아니다
        self.assertEqual(run(None, [("a.png", b"1"), ("b.png", b"2")], {"ingest.transcribe": [{"readable": True, "text": top}, {"readable": True, "text": bottom}]})[0], top + "\n\n| [4] | 4 |")

    def test_pdf_control_characters_become_spaces(self):
        from ..ingest.text import tidy

        self.assertEqual(tidy("출석부의\u0001단골  이름\n    들여쓰기\t탭"), "출석부의 단골 이름\n    들여쓰기\t탭")

    def test_join_order_and_encodings(self):
        docs = [("a.md", "﻿## 입력\n두 수".encode("utf-8")), ("b.txt", "## 출력\n합".encode("cp949")), ("c.txt", b"  ")]
        self.assertEqual(join_text(" 문제 ", docs), "문제\n\n## 입력\n두 수\n\n## 출력\n합")
        with self.assertRaises(IngestError) as caught:
            join_text("", [("bad.txt", b"\xff\xff\xff")])
        self.assertIn("bad.txt", str(caught.exception))

    def test_text_and_pdf_need_no_model(self):
        body, fake = run("문제", [("p.pdf", text_pdf("Sum two numbers")), ("a.md", "## 출력".encode())])
        self.assertEqual(body, "문제\n\nSum two numbers\n\n## 출력")
        self.assertEqual(fake.calls, [])

    def test_rejections(self):
        cases = [
            ([("scan.pdf", blank_pdf())], "scan.pdf에서 글을"),
            ([("broken.pdf", b"not a pdf")], "broken.pdf 파일을"),
            ([("a.docx", b"x")], "a.docx"),
            ([(f"{n}.png", b"x") for n in range(21)], "20장"),
            ([("a.txt", b"  ")], "비었어요"),
        ]
        for files, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(IngestError) as caught:
                    run("", files)
                self.assertIn(message, str(caught.exception))
                self.assertEqual(caught.exception.code, "ingest_failed")


class OcrTest(unittest.TestCase):
    def test_trust_rule_edges(self):
        self.assertFalse(ocr_ok("가" * 19))
        self.assertTrue(ocr_ok("가 " * 20))
        self.assertTrue(ocr_ok("가" * 18 + "□□"))
        self.assertFalse(ocr_ok("가" * 17 + "□□□"))

    def test_missing_tesseract_is_empty(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(run_ocr(b"img"), "")

    def test_model_reads_images_and_skips_tesseract(self):
        body, used, fake, ocr = run_note("글", [("a.png", b"one"), ("B.PNG", b"two")], {"ingest.transcribe": [{"readable": True, "text": "## 입력\n두 수"}, {"readable": True, "text": "## 출력\n합"}]})
        self.assertEqual((body, used, ocr), ("글\n\n## 입력\n두 수\n\n## 출력\n합", False, []))
        self.assertEqual([call["images"] for call in fake.calls], [[b"one"], [b"two"]])
        self.assertIn("지어내지", fakes.prompt(fake, "ingest.transcribe"))
        self.assertIn('출력: {"readable": true, "text"', fakes.prompt(fake, "ingest.transcribe"))

    def test_no_model_reads_with_tesseract(self):
        body, used, fake, ocr = run_note("", [("a.png", b"one"), ("b.png", b"two")], {"ingest.transcribe": [LlmNotConfigured("없음")] * 2}, [GOOD_OCR, SECOND_OCR])
        self.assertEqual((body, used, ocr), (f"{GOOD_OCR}\n\n{SECOND_OCR}", True, [b"one", b"two"]))
        with self.assertRaises(LlmNotConfigured):  # tesseract도 못 믿으면 연결 안내
            run_note("", [("a.png", b"img")], {"ingest.transcribe": [LlmNotConfigured("없음")]}, [""])

    def test_model_failure_falls_back_to_tesseract_then_fails_with_the_page(self):
        """AI가 있는데 한 장이 tesseract로 읽혀 글이 깨졌고 안내는 'AI를 연결하면…'이었다. 실패한 장은 한 번 더 읽고, 두 번 실패해야 tesseract(표시 ai_failed)."""
        for reply in (LlmTimeout("늦음"), {"readable": True, "text": "  "}, {"readable": True, "text": "[2번째 장이 보이지 않습니다. 제공된 이미지는 1장뿐입니다.]"},
                      {"readable": True, "text": "이미지가 없습니다."},
                      {"readable": False, "text": "죄송하지만 첨부된 그림을 확인할 수 없어요. 문제 글을 직접 붙여 주시겠어요?"},  # 읽지 못했다는 답은 글이 무엇이든 문제 글로 쓰지 않는다
                      {"text": "죄송하지만 첨부된 그림을 확인할 수 없어요. 문제 글을 직접 붙여 주시겠어요?"}):  # readable이 빠진 답은 읽었다고 짐작하지 않는다(형식 실패)
            body, used, fake, ocr = run_note("", [("a.png", b"one"), ("b.png", b"two")], {"ingest.transcribe": [{"readable": True, "text": "첫 장"}, reply, {"readable": True, "text": "둘째 장"}]})
            self.assertEqual((body, used, ocr, len(fake.calls)), ("첫 장\n\n둘째 장", False, [], 3))  # 둘째 읽기에서 읽었다
            body, used, _, ocr = run_note("", [("a.png", b"one"), ("b.png", b"two")], {"ingest.transcribe": [{"readable": True, "text": "첫 장"}, reply, reply]}, [GOOD_OCR])
            self.assertEqual((body, used, ocr), (f"첫 장\n\n{GOOD_OCR}", "ai_failed", [b"two"]))
            with self.assertRaises(IngestError) as caught:
                run_note("", [("a.png", b"one"), ("b.png", b"two")], {"ingest.transcribe": [{"readable": True, "text": "첫 장"}, reply, reply]}, [""])
            self.assertIn("2번째", str(caught.exception))


class OutlineTest(unittest.TestCase):
    """구획 나누기: 모델은 줄 구간만 짚고, 검사와 읽기는 모델 없이 한다. 읽기 파서는 부르는 쪽이 준다(여기서는 받은 조각을 남기는 가짜)."""

    LINES = ["메뉴", "합 구하기", "배열 numbers의 합을 반환한다.", "예를 들어 numbers가 [1, 2]이면 3을 반환한다.", "numbers | result", "[4] | 4", "댓글"]

    def setUp(self):
        import json
        from types import SimpleNamespace

        self.seen = []
        self.read = SimpleNamespace(table=lambda part: self.seen.append(("table", part)) or {"names": [], "cases": [], "skipped": 0},
                                    samples=lambda part: self.seen.append(("samples", part)) or {"names": [], "cases": [], "skipped": 0}, value=json.loads)

    def ask(self, *replies):
        from ..ingest import outline

        fake = FakeLlm({"ingest.outline": list(replies)})
        with use_llm(fake):
            return outline.ask(self.LINES, self.read), [call["params"]["model"] for call in fake.calls]

    def test_spans_cases_and_noise_are_checked_without_model(self):
        said = [{"line": 4, "args": ["[1, 2]"], "expected": "3"}, {"line": 4, "args": ["[9]"], "expected": "3"}, {"line": 4, "args": ["[1,"], "expected": "3"}]
        got, models = self.ask({"problem": True, "title": 2, "body": [[3, 4]], "table": [5, 6], "samples": [{"in": None, "out": [7, 7]}], "cases": said,
                                "noise": [[1, 1]], "mode": "function", "names": ["numbers", 3], "many": False})
        self.assertEqual(models, ["claude/claude-haiku-5-5"])
        self.assertEqual((got["title"], got["noise"]), (2, [[1, 1]]))
        self.assertEqual(got["function"], {"names": ["numbers"], "cases": [{"input": "[[1, 2]]", "expected": "3"}], "skipped": 0})  # 줄에 없는 값·못 읽는 값은 버린다
        self.assertEqual(self.seen, [("table", "numbers | result\n[4] | 4"), ("samples", "예제 출력 1\n댓글")])  # 표·예제 구간은 규칙 파서가 읽는다

    def test_bad_reply_tries_middle_once_then_rules_only(self):
        for bad in ({"problem": True, "body": [[0, 2]], "mode": "function"}, {"problem": True, "body": [[2, 4]], "noise": [[4, 5]], "mode": "function"},
                    {"problem": True, "body": [[2, 9]], "mode": "function"}, {"problem": True, "mode": "both"}, {"problem": True, "title": 1, "noise": [[1, 1]], "mode": "function"},
                    {"problem": True, "samples": [{"in": [2, 3]}], "mode": "program"}, {"mode": "function"},
                    {"problem": True, "noise": [[1, 5]], "mode": "program"}):  # 잡음이 60%를 넘으면 답을 버린다
            self.assertEqual(self.ask(bad, bad), (None, ["claude/claude-haiku-5-5", "claude/claude-sonnet-5-5"]), bad)
        got, models = self.ask(LlmTimeout("늦음"), {"problem": False, "mode": "function"})
        self.assertEqual((got["problem"], models), (False, ["claude/claude-haiku-5-5", "claude/claude-sonnet-5-5"]))
        self.assertEqual(self.ask(LlmNotConfigured("없음")), (None, ["claude/claude-haiku-5-5"]))

    def test_normalize_keeps_superscripts(self):
        from ..ingest.outline import normalize

        self.assertEqual(normalize("１ ≤ N ≤ 10⁵\r\na b​\rc　d −3"), "1 ≤ N ≤ 10⁵\na b\nc d -3")
