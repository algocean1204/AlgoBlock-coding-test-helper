"""과정 표의 '문제 나누기'(split)와 '검증 풀이'(verify)."""

import os
import unittest
from unittest import mock

from ..llm import themes

CLEAN = {"ANTHROPIC_API_KEY": "k", "OPENAI_API_KEY": "", "ALGOBLOCK_LLM_PROVIDER": "", "ALGOBLOCK_LLM_MODEL": "",
         **{f"ALGOBLOCK_THEME_{name}": "" for name in ("INGEST", "SPLIT", "VERIFY", "GUIDE", "READ", "BLOCKS")}}


class SplitVerifyThemeTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(themes.choose, {})
        self.addCleanup(themes.NEWEST.clear)
        patch = mock.patch.dict(os.environ, CLEAN)
        patch.start()
        self.addCleanup(patch.stop)

    def test_table_has_new_themes_and_tasks(self):
        self.assertEqual(themes.default("split"), ("small", "low"))
        self.assertEqual(themes.default("verify"), ("middle", "low"))
        self.assertEqual(themes.theme_of("ingest.outline"), "split")
        self.assertEqual(themes.theme_of("plan.brute"), "verify")
        self.assertEqual(themes.theme_of("plan.solve"), "guide")  # 풀이와 생성기는 그대로 풀이 가이드
        self.assertEqual(themes.theme_of("plan.cases"), "guide")
        self.assertEqual(themes.theme_of("ingest.transcribe"), "read")

    def test_pick_runs_for_new_themes(self):
        self.assertEqual(themes.pick("ingest.outline"), ("claude/claude-haiku-5-5", "low"))
        self.assertEqual(themes.pick("plan.brute"), ("claude/claude-sonnet-5-5", "low"))
        self.assertEqual(themes.pick("plan.solve"), ("claude/claude-haiku-5-5", "high"))
        for key in themes.THEMES:  # 어느 과정이든 pick이 죽지 않는다
            task = next((t for t, theme in themes.TASKS.items() if theme == key), key + ".x")
            themes.pick(task)

    def test_user_choice_and_env_for_new_themes(self):
        themes.choose({"verify": {"tier": "small", "effort": "high"}, "split": {"tier": "large"}})
        self.assertEqual(themes.pick("plan.brute"), ("claude/claude-haiku-5-5", "high"))
        self.assertEqual(themes.pick("ingest.outline"), ("claude/claude-opus-5-5", "low"))
        themes.choose({})
        os.environ["ALGOBLOCK_THEME_VERIFY"] = "claude/claude-opus-5-5:medium"
        self.assertEqual(themes.pick("plan.brute"), ("claude/claude-opus-5-5", "medium"))
        os.environ["ALGOBLOCK_THEME_SPLIT"] = "claude/claude-sonnet-5-5:high"
        self.assertEqual(themes.pick("ingest.outline"), ("claude/claude-sonnet-5-5", "high"))

    def test_old_settings_and_env_still_read(self):
        moved = themes.from_old({"ingest": {"model": "claude/claude-opus-5-5", "effort": "medium"}, "explain": {"model": "claude/claude-sonnet-5-5", "effort": ""}})
        self.assertEqual({key for key, row in moved.items() if row == {"tier": "large", "effort": "medium"}}, {"read", "guide", "blocks", "split", "verify"})
        self.assertEqual({moved["explain"]["tier"], moved["feedback"]["tier"]}, {"middle"})
        themes.choose(moved)
        self.assertEqual(themes.pick("plan.brute"), ("claude/claude-opus-5-5", "medium"))
        themes.choose({})
        os.environ["ALGOBLOCK_THEME_INGEST"] = "claude/claude-opus-5-5:medium"  # 예전 이름이 새 과정에도 간다
        self.assertEqual({themes.pick(t) for t in ("ingest.transcribe", "plan.solve", "plan.draft_blocks", "ingest.outline", "plan.brute")}, {("claude/claude-opus-5-5", "medium")})
        self.assertEqual(themes.pick("chair.ask"), ("claude/claude-haiku-5-5", "low"))
        os.environ["ALGOBLOCK_THEME_VERIFY"] = "claude/claude-haiku-5-5:high"  # 새 이름이 예전 이름보다 이긴다
        self.assertEqual(themes.pick("plan.brute"), ("claude/claude-haiku-5-5", "high"))


if __name__ == "__main__":
    unittest.main()
