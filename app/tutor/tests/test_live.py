"""실모델. ALGOBLOCK_LIVE=1일 때만 돈다. 키는 공급자 환경 변수(ANTHROPIC_API_KEY 등) 또는 ALGOBLOCK_LLM_API_KEY."""

import os
import unittest

from ..llm import llm, model_name
from ..state import Reply


@unittest.skipUnless(os.environ.get("ALGOBLOCK_LIVE") == "1", "ALGOBLOCK_LIVE=1일 때만")
class LiveTest(unittest.TestCase):
    def test_default_model_answers_a_schema(self):
        got = llm(model_name()).use([{"role": "user", "content": '한 단어로 인사해라. {"text": "..."} 모양으로.'}], Reply, task="live.ping")
        self.assertTrue(got.text.strip())
