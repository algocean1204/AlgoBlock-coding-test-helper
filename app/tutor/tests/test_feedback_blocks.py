import unittest

from ..feedback.rules import UNOPENED_FALLBACK, check_feedback, drop_unopened


class UnopenedBlockTest(unittest.TestCase):
    def test_sentences_naming_unopened_blocks_are_dropped(self):
        text = "제출 코드는 블록 4·5·6을 수행합니다. 블록 1은 입력을 읽습니다. 빈 입력이 들어오면 어떻게 될까요?"
        self.assertEqual(drop_unopened(text, 1), "블록 1은 입력을 읽습니다. 빈 입력이 들어오면 어떻게 될까요?")
        self.assertEqual(drop_unopened(text, 0), "빈 입력이 들어오면 어떻게 될까요?")  # 혼자 푼 풀이: 블록 말은 모두 뺀다

    def test_opened_blocks_and_code_words_are_kept(self):
        for text in ("3번 블록에서 반복 범위를 잡은 방식이 좋았어요.", "4~6번 블록에서 합을 구했어요.", "다음 블록에서 합을 구했어요.", "블록 2와 3을 열었어요."):
            self.assertEqual(drop_unopened(text, 6 if "2와" not in text else 3), text)
        self.assertEqual(drop_unopened("블록 2와 5를 봤어요.", 3), "")
        self.assertEqual(drop_unopened("7번 블록을 봤어요.", 6), "")
        for text in ("for 블록 안에서 합을 구해요.", "if 블록 안의 조건이 달라요.", "코드 블록 첫 줄을 보세요."):
            self.assertEqual(drop_unopened(text, 0), text)
        self.assertEqual(drop_unopened("블록 3을 봤어요.", 0), "")

    def test_check_feedback_replaces_empty_analysis(self):
        fields, _ = check_feedback("블록 3을 수행합니다.", "해시: 센다", "블록 2를 먼저 보세요. 경계를 보세요.", "해시", opened=0)
        self.assertIn(UNOPENED_FALLBACK, fields["analysis"])
        self.assertEqual(fields["advice"], "경계를 보세요.")
