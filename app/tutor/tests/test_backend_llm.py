"""공급자(app/llm, app.llm) 시험. tutor가 쓰는 모델 입구가 서버 안에서 그대로 도는지 본다."""

import json
import os
import unittest
from dataclasses import dataclass
from pathlib import Path

from ..llm.client import _backend_session

_session = _backend_session()  # 저장소 루트를 경로에 더해 app.llm을 부른다
from app.llm.openai.oauth.pkce import make_pkce  # noqa: E402
from app.llm.errors import LlmFailed  # noqa: E402
from app.llm.parse import parse, text_of  # noqa: E402
from app.llm.route import route  # noqa: E402
from app.llm.session import llm  # noqa: E402
from app.llm.wire import set_transport  # noqa: E402

LLM_ROOT = Path(_session.__file__).resolve().parent


@dataclass
class Reply:
    text: str


class ProviderTest(unittest.TestCase):
    def test_provider_folders_do_not_import_each_other(self):
        root = LLM_ROOT
        folders = {
            "openai/api_key": ["claude", "oauth"],
            "openai/oauth": ["claude", "api_key"],
            "claude/api_key": ["openai"],
        }
        for folder, banned in folders.items():
            for path in (root / folder).rglob("*.py"):
                text = path.read_text()
                for word in banned:
                    self.assertNotIn(word, text, f"{path.name} imports {word}")
    def tearDown(self):
        set_transport(None)

    def test_route_splits_auth(self):
        self.assertEqual(route("openai/gpt-5.4").auth, "api_key")
        self.assertEqual(route("chatgpt/gpt-5.4").auth, "oauth")
        self.assertEqual(route("claude/claude-sonnet-4", auth="oauth").auth, "api_key")
        self.assertEqual(route("grok/grok-4").provider, "")  # 걷어 낸 공급자는 연결되지 않은 이름이다

    def test_pkce_challenge_has_no_padding(self):
        verifier, challenge = make_pkce()
        self.assertGreater(len(verifier), 40)
        self.assertNotIn("=", challenge)

    def test_openai_key_posts_responses_and_parses(self):
        seen = {}

        def transport(url, headers, body, timeout):
            seen["url"] = url
            seen["headers"] = headers
            seen["body"] = body
            return {"output_text": '{"text": "안녕"}'}

        set_transport(transport)
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            got = llm("openai/gpt-5.4").use([{"role": "user", "content": "가"}], Reply)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        self.assertEqual(got.text, "안녕")
        self.assertEqual(seen["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(seen["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(seen["body"]["model"], "gpt-5.4")
        self.assertEqual(seen["body"]["input"][0]["role"], "user")

    def test_model_lists_are_get_requests(self):
        """모델 목록(최신 버전 고르기에 쓴다)은 키를 실은 GET이고, 응답에서 이름만 꺼낸다."""
        from app.llm.claude.api_key.messages import models as claude_models
        from app.llm.openai.api_key.chat import models as openai_models

        seen = []

        def transport(url, headers, body, timeout):
            seen.append((url, body, headers.get("x-api-key") or headers.get("Authorization")))
            return {"data": [{"id": "claude-haiku-5-5"}, {"id": 3}, {"name": "x"}]}

        set_transport(transport)
        os.environ.update(ANTHROPIC_API_KEY="ant-test", OPENAI_API_KEY="sk-test")
        try:
            self.assertEqual((claude_models(), openai_models()), (["claude-haiku-5-5"], ["claude-haiku-5-5"]))
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)
        self.assertEqual(seen, [("https://api.anthropic.com/v1/models?limit=1000", None, "ant-test"), ("https://api.openai.com/v1/models", None, "Bearer sk-test")])

    def test_claude_uses_messages_and_api_key_header(self):
        seen = {}

        def transport(url, headers, body, timeout):
            seen["url"] = url
            seen["headers"] = headers
            seen["body"] = body
            return {"content": [{"type": "text", "text": '{"text": "클로드"}'}]}

        set_transport(transport)
        os.environ["ANTHROPIC_API_KEY"] = "ant-test"
        try:
            got = llm("claude/claude-sonnet-4").use(
                [{"role": "system", "content": "규칙"}, {"role": "user", "content": "가"}],
                Reply,
            )
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertEqual(got.text, "클로드")
        self.assertEqual(seen["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(seen["headers"]["x-api-key"], "ant-test")
        self.assertEqual(seen["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(seen["body"]["system"], "규칙")
        self.assertEqual(seen["body"]["messages"][0]["role"], "user")

    def test_broken_json_is_asked_again_once(self):
        """긴 JSON에서 따옴표를 풀지 않은 답이 가끔 온다. 서버 오류로 새지 않게 하고 한 번 다시 받는다. 두 번 다 깨지면 llm_failed."""
        from app.llm.errors import LlmFailed

        answers = ['{"text": "닫는 괄호 "]"가 나오면"}', '{"text": "다시 받은 답"}', '{"text": "깨짐 "1""}', '{"text": "또 깨짐 "2""}']
        calls = []

        def transport(url, headers, body, timeout):
            calls.append(url)
            return {"content": [{"type": "text", "text": answers[len(calls) - 1]}]}

        set_transport(transport)
        os.environ["ANTHROPIC_API_KEY"] = "ant-test"
        try:
            self.assertEqual(llm("claude/claude-sonnet-4").use([{"role": "user", "content": "가"}], Reply).text, "다시 받은 답")
            self.assertEqual(len(calls), 2)
            with self.assertRaises(LlmFailed):
                llm("claude/claude-sonnet-4").use([{"role": "user", "content": "가"}], Reply)
            self.assertEqual(len(calls), 4)
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_parse_reads_responses_text(self):
        self.assertEqual(text_of({"output_text": "x"}), "x")
        self.assertEqual(parse(Reply, {"output_text": '{"text": "파서"}'}).text, "파서")

    def test_parse_reads_optional_fields_like_the_fake_client(self):
        """실제 공급자 경로와 가짜 모델의 검사 함수가 X | None 칸을 같게 읽는다(숨은 테스트 생성기의 제한사항이 이 꼴이다)."""
        from ..llm.client import coerce as fake_coerce
        from ..state import CaseMaker

        ok = {"code": "def small(): pass", "bounds": [{"arg": 0, "low": 1, "high": None, "longest": 5}]}
        got = parse(CaseMaker, {"output_text": json.dumps(ok)})
        self.assertEqual((got.bounds[0].low, got.bounds[0].high, got.bounds[0].longest), (1, None, 5))
        self.assertEqual(got, fake_coerce(CaseMaker, ok))
        bad = {"code": "x", "bounds": [{"arg": 0, "low": "많이"}]}
        with self.assertRaises(LlmFailed):
            parse(CaseMaker, {"output_text": json.dumps(bad)})
        from ..llm import client as fake  # 가짜 모델 쪽은 튜터의 오류 꼴로 알린다
        with self.assertRaises(fake.LlmFailed):
            fake_coerce(CaseMaker, bad)

    def test_parse_takes_loose_extra_fields(self):
        """모양을 따지지 않는 덤 필드(Any)는 공급자 파서도 그대로 받는다: 태그·단계의 모양 탓에 풀이 가이드 전체를 잃지 않는다."""
        import json

        from ..state import LabeledSolved

        for tags, level in ((None, "2"), ("bfs", 2.0), (["bfs"], None)):
            body = {"approach": "a", "steps": [], "code": "c", "tags": tags, "level": level}
            got = parse(LabeledSolved, {"output_text": json.dumps(body)})
            self.assertEqual((got.code, got.tags, got.level), ("c", tags, level))


class CacheTest(unittest.TestCase):
    """캐시 경계 표시(cache_prefix)가 공급자마다 맞는 모양으로 가는지, 사용량이 남는지."""

    def setUp(self):
        self.seen = {}

        def transport(url, headers, body, timeout):
            self.seen.update(url=url, headers=headers, body=body)
            if "anthropic" in url:
                return {"content": [{"type": "text", "text": "[check]Y"}],
                        "usage": {"input_tokens": 5, "cache_read_input_tokens": 900, "cache_creation_input_tokens": 0, "output_tokens": 3}}
            if "responses" in url:
                return {"output_text": "답", "usage": {"input_tokens": 1500, "input_tokens_details": {"cached_tokens": 1024}, "output_tokens": 2}}
            raise AssertionError(url)

        set_transport(transport)
        os.environ.update(ANTHROPIC_API_KEY="a", OPENAI_API_KEY="o")
        self.messages = [
            {"role": "system", "content": "규칙"},
            {"role": "user", "content": "문제:\n글\n지금 블록:b1", "cache_prefix": len("문제:\n글")},
        ]

    def tearDown(self):
        set_transport(None)
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ALGOBLOCK_LLM_CACHE_TTL"):
            os.environ.pop(key, None)

    def test_claude_marks_cache_boundary(self):
        from app.llm import usage

        llm("claude/claude-haiku-5-5").use(self.messages, None, task="chair.judge")
        blocks = self.seen["body"]["messages"][0]["content"]
        self.assertEqual(blocks[0], {"type": "text", "text": "문제:\n글", "cache_control": {"type": "ephemeral"}})
        self.assertEqual(blocks[1]["text"], "\n지금 블록:b1")
        self.assertNotIn("cache_prefix", str(self.seen["body"]))
        last = usage.RECENT[-1]
        self.assertEqual((last["task"], last["cache_read"], last["input"]), ("chair.judge", 900, 5))

    def test_usage_log_and_prompt_copy(self):
        """호출마다 기록 파일에 한 줄(글·키 없음), 모양 재요청은 retry. 프롬프트 사본은 ALGOBLOCK_LLM_PROMPT_DIR을 켰을 때만. 보고 스크립트가 묶는다."""
        import json
        import tempfile

        from ..eval.cost import report, summary

        folder = Path(tempfile.mkdtemp(prefix="algoblock-usage-"))
        log, copies = folder / "usage.jsonl", folder / "prompts"
        answers = ['{"text": "깨짐 "1""}', '{"text": "다시"}']
        set_transport(lambda *a: {"content": [{"type": "text", "text": answers.pop(0)}], "usage": {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}})
        os.environ["ALGOBLOCK_LLM_USAGE_LOG"] = str(log)
        try:
            llm("claude/claude-haiku-5-5").use(self.messages, Reply, task="chair.ask", effort="low")
            self.assertFalse(copies.exists())  # 기본은 꺼짐
            os.environ["ALGOBLOCK_LLM_PROMPT_DIR"] = str(copies)
            answers[:] = ['{"text": "하나"}']
            llm("claude/claude-haiku-5-5").use(self.messages, Reply, task="chair.ask")
        finally:
            os.environ.pop("ALGOBLOCK_LLM_USAGE_LOG", None)
            os.environ.pop("ALGOBLOCK_LLM_PROMPT_DIR", None)
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(r["task"], r["retry"], r["effort"], r["cache_read"]) for r in rows], [("chair.ask", False, "low", 90), ("chair.ask", True, "low", 90), ("chair.ask", False, None, 90)])
        self.assertNotIn("문제", log.read_text(encoding="utf-8"))  # 프롬프트 글은 적지 않는다
        kept = json.loads(next(copies.iterdir()).read_text(encoding="utf-8"))
        self.assertEqual((kept["task"], kept["messages"][1]["content"]), ("chair.ask", "문제:\n글\n지금 블록:b1"))
        s = summary(rows)
        self.assertEqual((s["calls"], s["retries"], round(s["hit"], 2)), (3, 1, 0.9))
        self.assertAlmostEqual(s["usd"], 3 * (10 * 0.10 + 90 * 0.01 + 5 * 0.50) / 1e6)
        self.assertIn("| 흐름1 | 3 | 1 |", report(rows, [{"flow": "흐름1", "start": 0, "end": 1e12}]))

    def test_dev_client_calls_are_recorded_with_task_names(self):
        """개발용 연결(이 PC의 Claude Code)의 호출도 같은 기록 파일에 남는다: 과정 이름과 호출 수, 금액은 0."""
        import json
        import subprocess
        import tempfile
        from types import SimpleNamespace
        from unittest import mock

        from ..eval.cli_client import ClaudeCli
        from ..eval.cost import summary

        log = Path(tempfile.mkdtemp(prefix="algoblock-usage-")) / "usage.jsonl"
        said = json.dumps({"result": '{"text": "답"}', "usage": {"input_tokens": 3, "cache_read_input_tokens": 7, "output_tokens": 2}})
        os.environ["ALGOBLOCK_LLM_USAGE_LOG"] = str(log)
        try:
            with mock.patch.object(subprocess, "run", return_value=SimpleNamespace(stdout=said, stderr="")):
                client = ClaudeCli()
                client.run("plan.solve", [{"role": "user", "content": "x"}], Reply, params={"model": "claude-sonnet-5-5", "effort": "high"})
                client.run("feedback.analyze", [{"role": "user", "content": "x"}], Reply, params={"model": "claude-haiku-5-5"})
        finally:
            os.environ.pop("ALGOBLOCK_LLM_USAGE_LOG", None)
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(r["task"], r["model"], r["effort"], r["cache_read"]) for r in rows], [("plan.solve", "cli/sonnet", "high", 7), ("feedback.analyze", "cli/haiku", None, 7)])
        self.assertEqual((summary(rows)["calls"], summary(rows)["usd"]), (2, 0.0))

    def test_claude_ttl_one_hour(self):
        os.environ["ALGOBLOCK_LLM_CACHE_TTL"] = "1h"
        llm("claude/claude-haiku-5-5").use(self.messages, None)
        self.assertEqual(self.seen["body"]["messages"][0]["content"][0]["cache_control"]["ttl"], "1h")

    def test_short_answer_gets_thinking_room_and_effort(self):
        """Haiku 5.5는 생각이 기본으로 켜져 16토큰 판정이 빈 글로 온다. 짧은 답에는 생각 몫을 더하고 effort를 보낸다."""
        llm("claude/claude-haiku-5-5").use(self.messages, None, max_tokens=16, effort="low")
        self.assertEqual(self.seen["body"]["max_tokens"], 16 + 2048)
        self.assertEqual(self.seen["body"]["output_config"], {"effort": "low"})
        self.assertNotIn("temperature", self.seen["body"])
        self.assertNotIn("thinking", self.seen["body"])
        llm("claude/claude-haiku-5-5").use(self.messages, None, effort="high")  # 긴 답
        self.assertEqual((self.seen["body"]["max_tokens"], self.seen["body"]["output_config"]), (16000, {"effort": "high"}))

    def test_truncated_or_refused_answer_is_an_error(self):
        from app.llm.errors import LlmFailed

        set_transport(lambda *a: {"content": [{"type": "text", "text": '{"blocks": ['}], "stop_reason": "max_tokens"})
        with self.assertRaises(LlmFailed):
            llm("claude/claude-haiku-5-5").use(self.messages, None)

    def test_openai_gets_prompt_cache_key_and_cached_tokens(self):
        from app.llm import usage

        llm("openai/gpt-5.4").use(self.messages, None, task="chair.ask")
        key = self.seen["body"]["prompt_cache_key"]
        self.assertEqual(len(key), 32)
        llm("openai/gpt-5.4").use([self.messages[0], {**self.messages[1], "content": "문제:\n글\n지금 블록:b2"}], None)
        self.assertEqual(self.seen["body"]["prompt_cache_key"], key)  # 앞부분이 같으면 같은 키
        self.assertEqual((usage.RECENT[-1]["cache_read"], usage.RECENT[-1]["input"]), (1024, 476))
