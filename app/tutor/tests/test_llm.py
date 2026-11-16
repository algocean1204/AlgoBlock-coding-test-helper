"""모델 입구: 모양 맞추기, 가짜 모델, backend 공급자 연결."""

import json
import os
import unittest
from unittest import mock

from . import fakes
from ..llm import FakeLlm, LlmFailed, LlmNotConfigured, LlmTimeout, coerce, llm, model_name, use_llm
from ..llm.client import _backend_session
from ..state import Block, DraftedBlocks, Reply


class LlmTest(unittest.TestCase):
    def test_coerce_nested_defaults_and_reject_shape(self):
        got = coerce(DraftedBlocks, {**fakes.drafted([fakes.as_dict(fakes.two()[0])]), "extra": 1})
        self.assertEqual(got.blocks[0].name, "입력받기")
        made = coerce(Block, {"id": "b1", "kind": "loop", "name": "n", "goal": "g", "reference": "r"})
        self.assertEqual((made.checks, made.hints), ([], []))
        for bad in ({"nope": 1}, {"text": 1}):
            with self.assertRaises(LlmFailed):
                coerce(Reply, bad)

    def test_fake_records_order_text_mode_and_timeout(self):
        fake = FakeLlm({"a.task": [{"text": "하나"}, "둘"]})
        with use_llm(fake):
            self.assertEqual(llm("x").use([{"role": "user", "content": "가"}], Reply, task="a.task").text, "하나")
            self.assertEqual(llm("x").use([{"role": "user", "content": "나"}], None, task="a.task", max_tokens=16), "둘")
        self.assertEqual(fake.calls[1]["params"]["max_tokens"], 16)
        with self.assertRaises(LlmFailed):
            FakeLlm({"t": [{"text": "x"}]}).run("t", [], None)
        with mock.patch.dict(os.environ, {"ALGOBLOCK_LLM_TIMEOUT": "1"}):
            with self.assertRaises(LlmTimeout):
                FakeLlm(delay=2).run("a.task", [], Reply)

    def test_provider_status_maps_to_error_code(self):
        from ..common.errors import STATUS, llm_error

        for exc, code in ((LlmNotConfigured("키를 확인해 주세요(401)."), "llm_auth_failed"), (LlmNotConfigured("키를 확인해 주세요(403)."), "llm_auth_failed"),
                          (LlmFailed("공급자 오류(429)"), "llm_rate_limited"), (LlmNotConfigured("모델이나 키가 없습니다."), "llm_not_configured"),
                          (LlmFailed("공급자 오류(500)"), "llm_failed"), (LlmTimeout("60초를 넘겼습니다."), "llm_timeout")):
            self.assertEqual(llm_error(exc).code, code)
        self.assertEqual((STATUS["llm_auth_failed"], STATUS["llm_rate_limited"]), (401, 429))
        self.assertEqual(llm_error(LlmFailed("공급자 오류(429)")).message, "모델 사용 한도에 걸렸어요. 잠시 뒤에 다시 해 주세요.")
        self.assertEqual(llm_error(LlmFailed("ChatGPT 사용 한도에 걸렸어요.(429)")).message, "ChatGPT 사용 한도에 걸렸어요.")  # 공급자 경로가 실은 안내

    def test_backend_errors_map(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "", "ALGOBLOCK_LLM_API_KEY": ""}):
            with self.assertRaises(LlmNotConfigured):
                llm("openai/gpt-5.4").use([{"role": "user", "content": "가"}], Reply, task="a")
        with self.assertRaises(LlmFailed) as caught:
            llm("local-model").use([{"role": "user", "content": "가"}], Reply, task="a")
        self.assertIn("공급자", str(caught.exception))

    def test_default_model_goes_to_claude_haiku_and_text_mode_has_no_json_hint(self):
        wire = __import__("app.llm.wire", fromlist=["set_transport"]) if _backend_session() else None
        seen = []

        def transport(url, headers, body, timeout):
            seen.append(body)
            return {"content": [{"type": "text", "text": '{"text": "안녕"}' if len(seen) == 1 else "[check]N2"}]}

        wire.set_transport(transport)
        try:
            with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "ant-test"}):
                os.environ.pop("ALGOBLOCK_LLM_MODEL", None)
                got = llm(model_name()).use([{"role": "user", "content": "가"}], Reply, task="a")
                text = llm(model_name()).use([{"role": "user", "content": "판정"}], None, task="b", max_tokens=16)
        finally:
            wire.set_transport(None)
        self.assertEqual(got.text, "안녕")
        self.assertEqual(seen[0]["model"], "claude-haiku-5-5")
        self.assertEqual(text, "[check]N2")
        self.assertEqual(seen[1]["max_tokens"], 16 + 2048)  # 짧은 답에는 생각 몫을 더한다
        self.assertNotIn("JSON", str(seen[1]["messages"]))


class ThemeTest(unittest.TestCase):
    """task 이름이 과정을 정하고, 과정이 급과 추론 정도를 정한다. 급은 지금 연결의 그 시리즈 최신 이름으로 풀린다."""

    def setUp(self):
        from ..llm import themes

        self.addCleanup(themes.choose, {})
        self.addCleanup(themes.NEWEST.clear)

    def test_task_picks_theme(self):
        from ..llm import themes

        self.assertEqual([themes.theme_of(task) for task in ("ingest.transcribe", "plan.abstract", "plan.assess", "plan.solve")], ["read", "guide", "guide", "guide"])
        self.assertEqual([themes.theme_of(task) for task in ("plan.gate", "plan.draft_blocks", "plan.hints", "eval.judge")], ["blocks"] * 4)  # 평가기는 튜터의 판정보다 센 모델을 쓴다
        self.assertEqual([themes.theme_of(task) for task in ("chair.judge", "guide.check_code", "debug.judge")], ["judge"] * 3)
        self.assertEqual([themes.theme_of(task) for task in ("explain.write", "feedback.assess", "feedback.analyze", "debug.locate")], ["explain", "feedback", "feedback", "debug"])
        self.assertEqual([themes.theme_of(task) for task in ("chair.ask", "debug.ask", "새로운.작업", None)], ["talk"] * 4)
        clean = {"ANTHROPIC_API_KEY": "k", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": "", "ALGOBLOCK_THEME_EXPLAIN": "", "ALGOBLOCK_THEME_FEEDBACK": "", "ALGOBLOCK_THEME_INGEST": "", "ALGOBLOCK_THEME_GUIDE": ""}
        with mock.patch.dict(os.environ, clean):
            self.assertEqual(themes.pick("plan.solve"), ("claude/claude-haiku-5-5", "high"))  # 풀이 가이드는 작은 급·high(채점과 대조가 확인한다)
            self.assertEqual(themes.pick("ingest.transcribe"), ("claude/claude-sonnet-5-5", "high"))  # 문제 읽기는 가운데 급
            self.assertEqual(themes.pick("chair.ask"), ("claude/claude-haiku-5-5", "low"))
            self.assertEqual(themes.pick("explain.write"), ("claude/claude-haiku-5-5", "medium"))
            os.environ["ALGOBLOCK_THEME_EXPLAIN"] = "claude/claude-sonnet-5-5:low"  # 측정용 환경 변수. 예전 이름 EXPLAIN은 해설·피드백 둘에 간다
            self.assertEqual((themes.pick("explain.write"), themes.pick("feedback.analyze")), (("claude/claude-sonnet-5-5", "low"),) * 2)
            os.environ["ALGOBLOCK_THEME_FEEDBACK"] = "claude/claude-opus-5-5:high"  # 새 이름이 이긴다
            self.assertEqual(themes.pick("feedback.analyze"), ("claude/claude-opus-5-5", "high"))
            os.environ["ALGOBLOCK_THEME_INGEST"] = "claude/claude-opus-5-5:medium"  # make_builtin·ingest_bench가 쓰는 예전 이름
            self.assertEqual({themes.pick(task) for task in ("ingest.transcribe", "plan.solve", "plan.draft_blocks")}, {("claude/claude-opus-5-5", "medium")})
            self.assertEqual(themes.pick("chair.ask"), ("claude/claude-haiku-5-5", "low"))
            os.environ["ALGOBLOCK_LLM_MODEL"] = "openai/gpt-5.4"  # 모든 task를 한 모델로
            self.assertEqual(themes.pick("explain.write")[0], "openai/gpt-5.4")

    def test_user_choice_overrides_defaults(self):
        """사용자가 과정마다 급과 추론 정도를 고른다. 빈 값은 기본값, 모르는 과정·급·정도는 버린다."""
        from ..llm import themes

        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": ""}):
            themes.choose({"talk": {"tier": "middle", "effort": "medium"}, "guide": {"tier": "", "effort": "low"}, "blocks": {"tier": "large"},
                           "judge": {"tier": "아주 큼", "effort": "아주 높음"}, "없는 과정": {"tier": "small"}})
            self.assertEqual(themes.pick("chair.ask"), ("claude/claude-sonnet-5-5", "medium"))
            self.assertEqual(themes.pick("plan.solve"), ("claude/claude-haiku-5-5", "low"))  # 급은 기본값(작음), 정도만 고른 값
            self.assertEqual(themes.pick("plan.draft_blocks"), ("claude/claude-opus-5-5", "high"))  # 큼은 기본값이 아니지만 고를 수 있다
            self.assertEqual(themes.pick("chair.judge"), ("claude/claude-haiku-5-5", "low"))
            self.assertNotIn("없는 과정", themes.CHOSEN)
            os.environ.update(ANTHROPIC_API_KEY="", OPENAI_API_KEY="k")  # 연결을 바꿔도 고른 급이 그대로 간다
            self.assertEqual((themes.pick("chair.ask"), themes.pick("plan.draft_blocks")), (("openai/gpt-6.1-terra", "medium"), ("openai/gpt-6.1-sol", "high")))
            themes.choose({})
            self.assertEqual(themes.pick("chair.ask"), ("openai/gpt-6-luna", "low"))

    def test_old_settings_move_to_tiers(self):
        """예전 테마 다섯(모델 이름)은 새 과정의 급으로 옮긴다. 표에 없는 이름(Grok·OpenRouter, 직접 적은 이름)은 조용히 버리고 기본값을 쓴다."""
        from ..llm import themes

        moved = themes.from_old({"ingest": {"model": "claude/claude-opus-5-5", "effort": "medium"}, "explain": {"model": "grok/grok-5", "effort": "high"},
                                 "talk": {"model": "openrouter/x-ai/grok-4", "effort": ""}, "judge": {"model": "chatgpt/gpt-6-luna"}, "debug": "망가짐", "없는 테마": {}})
        self.assertEqual(moved, {**{key: {"tier": "large", "effort": "medium"} for key in ("read", "guide", "blocks")},
                                 **{key: {"tier": "", "effort": "high"} for key in ("explain", "feedback")},
                                 "talk": {"tier": "", "effort": ""}, "judge": {"tier": "small", "effort": ""}})
        self.assertEqual(themes.from_old(None), {})

    def test_newest_version_in_each_series(self):
        """연결의 모델 목록에서 시리즈마다 가장 높은 버전을 고른다. 날짜 붙은 스냅숏과 꼴이 다른 이름은 건너뛴다. 목록이 없으면 표의 이름."""
        from ..llm import themes

        names = ["claude-haiku-5-5", "claude-haiku-5-6-20270101", "claude-sonnet-5-5", "claude-sonnet-5-6", "claude-sonnet-4-20250514", "claude-opus-5",
                 "claude-sonnet-5-6-preview", "gpt-6-luna", "gpt-6.1-terra", "gpt-6.2-terra-2027-01-01", "gpt-6-astra", 3]
        self.assertEqual(themes.newest(names), {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-6", "opus": "claude-opus-5", "luna": "gpt-6-luna", "terra": "gpt-6.1-terra"})
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": "", "ALGOBLOCK_THEME_INGEST": "", "ALGOBLOCK_THEME_GUIDE": ""}):
            self.assertEqual(themes.pick("ingest.transcribe")[0], "claude/claude-sonnet-5-5")  # 목록을 받지 못했다: 표의 이름
            themes.NEWEST["claude"] = themes.newest(names)
            self.assertEqual(themes.pick("ingest.transcribe")[0], "claude/claude-sonnet-5-6")
            self.assertEqual(themes.pick("chair.ask")[0], "claude/claude-haiku-5-5")
        self.assertEqual([themes.label(name) for name in ("claude/claude-sonnet-5-5", "claude/claude-opus-5", "openai/gpt-6.1-terra", "chatgpt/gpt-6-luna")],
                         ["Sonnet 5.5", "Opus 5", "Terra (GPT-6.1)", "Luna (GPT-6)"])

    def test_provider_picks_series(self):
        """Claude 키 → Claude 시리즈, ChatGPT 구독 로그인·OpenAI 키 → OpenAI 시리즈(같은 급)."""
        import tempfile
        from pathlib import Path

        from ..llm import themes

        clean = {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": "", "ALGOBLOCK_LLM_AUTH_DIR": "", "ALGOBLOCK_THEME_INGEST": "", "ALGOBLOCK_THEME_BLOCKS": ""}
        with mock.patch.dict(os.environ, clean):
            self.assertEqual(themes.pick("chair.ask"), ("claude/claude-haiku-5-5", "low"))
            with tempfile.TemporaryDirectory() as folder:
                os.environ["ALGOBLOCK_LLM_AUTH_DIR"] = folder
                (Path(folder) / "openai-oauth.json").write_text('{"access_token": "x"}')  # 예전 방식의 토큰은 연결로 보지 않는다
                self.assertEqual(themes.provider(), "claude")
                (Path(folder) / "chatgpt.json").write_text(json.dumps({"refresh_token": "r", "scopes": ["openid"]}))  # 요금제 사용을 허락받지 않음
                self.assertEqual(themes.provider(), "claude")
                (Path(folder) / "chatgpt.json").write_text(json.dumps({"refresh_token": "r", "scopes": ["chatgpt.tokens.use.direct", "openid"]}))
                self.assertEqual(themes.pick("ingest.transcribe"), ("chatgpt/gpt-6.1-terra", "high"))
                os.environ["ANTHROPIC_API_KEY"] = "k"  # Claude 키가 있으면 Claude가 먼저
                self.assertEqual(themes.provider(), "claude")
                os.environ["ALGOBLOCK_LLM_PROVIDER"] = "chatgpt"
                self.assertEqual(themes.pick("chair.judge"), ("chatgpt/gpt-6-luna", "low"))

    def test_use_passes_model_and_effort(self):
        from ..llm import FakeLlm, llm, use_llm

        fake = FakeLlm({"chair.judge": ["[check]Y"]})
        with use_llm(fake):
            llm().use([{"role": "user", "content": "x"}], None, task="chair.judge", max_tokens=16)
        params = fake.calls[0]["params"]
        self.assertEqual((params["model"], params["effort"], params["max_tokens"]), ("claude/claude-haiku-5-5", "low", 16))
