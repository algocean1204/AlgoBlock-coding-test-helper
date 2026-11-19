"""되물음의 답이 어느 블록의 말로 저장되는가. 되묻는 말과 그 답은 엔진이 답을 지은 블록(지금 블록)의 번호로 남는다.
앞 블록을 다시 확인받은 직후에 되물어도 답은 지금 블록의 질문으로 돌아오므로, 화면의 블록 번호 표도 지금 블록이어야 한다.
되물음 한 쌍이 지금 블록의 기록에 남아야 다음 턴의 문맥(직전 사용자 말, 최근 대화)이 그대로다."""

import re
import unittest

from .test_advance_rule import ASK, BLOCKS, CASES, HINTS, N, PASS, checked, context, said
from .test_auto_followup import EXPLAIN, GRAMMAR, chain
from .test_pipeline import exec_check
from ..common.talk_rules import FILL_TIP
from . import fakes


class QuestionAfterRecheckTest(unittest.TestCase):
    def test_answer_keeps_the_block_it_was_made_for(self):
        """지금 블록 i에서 '모르겠어요'로 힌트 2를 받고, 앞 블록 j를 다시 확인해 통과한 뒤(진행 그대로) 되물으면 말과 답(칸 포함)은 답을 지은 블록 i의 번호이고 진행은 그대로다.
        이어지는 '모르겠어요'는 i의 다음 저장 힌트만 받는다(되물음이 i의 기록에서 빠지면 직전 말이 앞의 '모르겠어요'가 되어 '이 블록 채우기' 안내 줄이 더 붙었다)."""
        names = [b.name for b in BLOCKS]
        for mode in ("chair", "guide"):
            for i in range(1, N):
                for j in range(i):
                    with self.subTest(mode=mode, current=i + 1, rechecked=j + 1):
                        out, _ = chain(mode, context(mode, i), [(said(mode, "모르겠어요"), {}, None),
                                                                (checked(mode, j, PASS), {}, exec_check([], CASES)),
                                                                (said(mode, GRAMMAR), {f"{mode}.judge": ["[check]Q"], ASK[mode]: [EXPLAIN]}, None),
                                                                (said(mode, "모르겠어요"), {}, None)])
                        (first, _, _), (rechecked, _, rows1), (asked, fake, rows2), (stuck, _, _) = out
                        self.assertEqual(first["result"]["reply"], HINTS[i][1])
                        self.assertEqual((rechecked["open_count"], rows1[-1]["block_index"]), (i + 1, j))  # 앞 블록 확인은 진행을 바꾸지 않고 그 블록의 말을 남긴다
                        self.assertEqual((asked["open_count"], asked["result"]["advance"], asked["result"]["move"]), (i + 1, False, "term"))
                        made_for = names.index(re.search(r"물을 블록:(.+?) \(", fakes.prompt(fake, ASK[mode])).group(1))
                        self.assertEqual(made_for, i)
                        self.assertEqual([r["role"] for r in rows2], ["user", "service"])
                        self.assertEqual([rows2[0]["block_index"], rows2[1]["block_index"], rows2[1]["parts"]["block_index"]], [made_for] * 3)
                        self.assertEqual((stuck["open_count"], stuck["result"]["reply"]), (i + 1, HINTS[i][2]))
                        self.assertNotIn(FILL_TIP.strip(), stuck["result"]["reply"])


if __name__ == "__main__":
    unittest.main()
