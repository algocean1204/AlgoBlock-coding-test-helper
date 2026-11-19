"""되물음의 답이 어느 블록의 말로 저장되는가. 되묻는 말과 그 답은 되물은 튜터 말의 블록 번호를 잇는다.
앞 블록을 다시 확인받은 직후에는 마지막 튜터 말이 앞 블록의 것이라, 지금 블록 번호로 저장되면 화면의 블록 번호 표가 어긋난다."""

import unittest

from .test_advance_rule import ASK, CASES, N, PASS, checked, context, said
from .test_auto_followup import EXPLAIN, GRAMMAR, chain
from .test_pipeline import exec_check


class QuestionAfterRecheckTest(unittest.TestCase):
    def test_answer_keeps_the_block_of_the_quoted_tutor_line(self):
        """지금 블록 i, 앞 블록 j를 다시 확인해 통과한 뒤(진행 그대로) 되물으면 말과 답은 j의 번호를 잇고 진행은 그대로다."""
        for mode in ("chair", "guide"):
            for i in range(1, N):
                for j in range(i):
                    with self.subTest(mode=mode, current=i + 1, rechecked=j + 1):
                        out, _ = chain(mode, context(mode, i), [(checked(mode, j, PASS), {}, exec_check([], CASES)),
                                                                (said(mode, GRAMMAR), {f"{mode}.judge": ["[check]Q"], ASK[mode]: [EXPLAIN]}, None)])
                        (rechecked, _, rows1), (asked, _, rows2) = out
                        self.assertEqual((rechecked["open_count"], rows1[-1]["block_index"]), (i + 1, j))  # 앞 블록 확인은 진행을 바꾸지 않고 그 블록의 말을 남긴다
                        self.assertEqual((asked["open_count"], asked["result"]["advance"]), (i + 1, False))
                        self.assertEqual([r["block_index"] for r in rows2], [j, j])


if __name__ == "__main__":
    unittest.main()
