import unittest

from ..feedback.rules import UNOPENED_FALLBACK, check_feedback, drop_unopened


class UnopenedBlockTest(unittest.TestCase):
    def test_sentences_naming_unopened_blocks_are_dropped(self):
        text = "제출 코드는 블록 4·5·6을 수행합니다. 블록 1은 입력을 읽습니다. 빈 입력이 들어오면 어떻게 될까요?"
        self.assertEqual(drop_unopened(text, 1), "블록 1은 입력을 읽습니다. 빈 입력이 들어오면 어떻게 될까요?")
        self.assertEqual(drop_unopened(text, 0), "빈 입력이 들어오면 어떻게 될까요?")  # 혼자 푼 풀이: 블록 말은 모두 뺀다

    def test_check_feedback_replaces_empty_analysis(self):
        fields, _ = check_feedback("블록 3을 수행합니다.", "해시: 센다", "블록 2를 먼저 보세요. 경계를 보세요.", "해시", opened=0)
        self.assertIn(UNOPENED_FALLBACK, fields["analysis"])
        self.assertEqual(fields["advice"], "경계를 보세요.")
