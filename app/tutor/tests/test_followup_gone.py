"""꼬리질문 기능은 엔진에 없다. 옛 꼬리질문 기록을 읽는 길(FollowupThread, 저장소의 quote 스레드)과 다른 과정은 그대로다."""
import importlib
import unittest

from .. import main, state
from ..llm import themes


class FollowupGone(unittest.TestCase):
    def test_no_followup_feature_or_kind(self):
        self.assertNotIn("followup", main.FEATURES)
        self.assertNotIn("followup", state.KINDS)
        self.assertFalse(hasattr(main.Tutor, "followup"))
        self.assertNotIn("followup", main.default_agents())

    def test_no_followup_graph_module(self):
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("tutor.followup.graph")

    def test_course_table_has_no_followup_and_keeps_the_rest(self):
        self.assertFalse([task for task in themes.TASKS if task.startswith("followup")])
        self.assertEqual(set(themes.THEMES), {"split", "read", "guide", "verify", "blocks", "talk", "judge", "explain", "feedback", "debug"})
        self.assertEqual(themes.theme_of("explain.write"), "explain")
        self.assertEqual(themes.theme_of("plan.hints"), "blocks")
        self.assertEqual(themes.theme_of("chair.ask"), "talk")
        self.assertEqual(themes.theme_of("anything.judge"), "judge")

    def test_old_thread_type_is_still_readable(self):
        thread = state.FollowupThread(quote_id="m1")
        self.assertEqual(thread.messages, [])
        self.assertTrue(hasattr(state.TutorContext, "__dataclass_fields__") and "followups" in state.TutorContext.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
