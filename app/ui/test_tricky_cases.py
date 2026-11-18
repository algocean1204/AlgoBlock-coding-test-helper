"""숨은 테스트의 함정 입력과 느린 풀이 확인(casemake, 실제 채점기, 모델 0회).

실행: cd app && python3.14 -B ui/test_tricky_cases.py
새로 지은 작은 문제(정수 배열의 합) 하나로 본다. 생성기·단순 풀이는 모델이 쓴 것처럼 미리 적어 둔 코드다.
계약: make()의 same 결과는 tags(hidden과 같은 길이, 'edge'·'tricky'·'random'), counts(edge·tricky·random·efficiency 수),
indistinct(단순 풀이가 큰 입력을 모두 끝냈다: 효율성으로 가리지 못함)를 더 갖는다. 생성기에 tricky()가 없어도 돈다.
"""

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import casegen  # noqa: E402
import casemake  # noqa: E402
from tutor.state import Bound  # noqa: E402

BOUNDS = [Bound(arg=0, low=-1000, high=1000, shortest=1, longest=100000)]
SOLUTION = "def solution(a):\n    total = 0\n    for number in a:\n        total += number\n    return total"
BRUTE = "def solution(a):\n    return sum(a)"
SLOW_ON_BIG = "def solution(a):\n    if len(a) > 1000:\n        while True:\n            pass\n    return sum(a)"
SMALL = ("import random\ndef small():\n    return [[[random.randint(10, 99) for _ in range(random.randint(1, 8))]] for _ in range(21)]\n"
         "def edge():\n    return [[[-1000]], [[1000, 1000, 1000]], [[7]]]\n"
         "def large():\n    return [[[random.randint(-1000, 1000) for _ in range(20000)]]]\n")
TRICKY = "def tricky():\n    return [[[0, 0, 0]], [[1000, -1000]], [[-1, -1, -1]], [[5000]]]\n"  # 마지막은 제한사항(1,000 이하)을 어겼다


def make(maker: str, code: str = SOLUTION, brute: str = BRUTE) -> dict:
    return casemake.make("python", "function", code, brute, maker, BOUNDS, 1)


class TrickyTest(unittest.TestCase):
    def test_generator_without_tricky_still_runs(self):
        found = make(SMALL)
        self.assertEqual(found["status"], "same", found)
        self.assertEqual(found["counts"]["tricky"], 0)
        self.assertEqual(set(found["tags"]), {"edge", "random"})
        self.assertEqual(len(found["tags"]), len(found["hidden"]))
        self.assertEqual(casemake.generate(SMALL)["tricky"], [])  # 없는 함수는 빈 목록

    def test_tricky_inputs_are_used_and_out_of_range_ones_dropped(self):
        found = make(SMALL + TRICKY)
        self.assertEqual(found["status"], "same", found)
        given = dict(found["hidden"])
        for one, want in (("[[0, 0, 0]]", "0"), ("[[1000, -1000]]", "0"), ("[[-1, -1, -1]]", "-3")):
            self.assertEqual(given.get(one), want, one)  # 기대값은 단순 풀이를 돌린 결과다
        self.assertNotIn("[[5000]]", given)
        self.assertEqual(found["dropped"], 1)
        self.assertEqual(found["counts"]["tricky"], 3)

    def test_tricky_input_alone_can_catch_a_wrong_solution(self):
        wrong = "def solution(a):\n    return sum(a) if any(a) else 1"  # 0만 있는 입력에서만 틀린다(경계·무작위에는 없다)
        self.assertEqual(make(SMALL, code=wrong)["status"], "same")
        found = make(SMALL + TRICKY, code=wrong)
        self.assertEqual(found["status"], "differ", found)
        self.assertEqual(found["input"], "[[0, 0, 0]]")

    def test_hidden_order_is_edge_then_tricky_then_random_round_robin(self):
        found = make(SMALL + TRICKY)
        self.assertEqual(len(found["hidden"]), casemake.HIDDEN_MAX)
        self.assertEqual(found["tags"][:9], ["edge", "tricky", "random"] * 3)
        self.assertEqual(set(found["tags"][9:]), {"random"})  # 경계·함정이 바닥나면 무작위로 채운다
        self.assertEqual({key: found["counts"][key] for key in ("edge", "tricky", "random")}, {"edge": 3, "tricky": 3, "random": 14})
        self.assertEqual(found["counts"]["efficiency"], len(found["large"]))

    def test_summary_counts_add_up(self):
        found = make(SMALL + TRICKY)
        counts = found["counts"]
        self.assertEqual(counts["edge"] + counts["tricky"] + counts["random"], len(found["hidden"]))
        self.assertEqual({tag: found["tags"].count(tag) for tag in ("edge", "tricky", "random")}, {key: counts[key] for key in ("edge", "tricky", "random")})

    def test_brute_that_finishes_the_big_input_is_not_distinguishing(self):
        found = make(SMALL + TRICKY)  # 단순 풀이가 큰 입력도 바로 끝낸다
        self.assertEqual((found["status"], found["indistinct"]), ("same", True), found)

    def test_brute_that_cannot_finish_the_big_input_distinguishes(self):
        found = make(SMALL + TRICKY, brute=SLOW_ON_BIG)  # 제한(10초)을 다 써 오래 걸린다
        self.assertEqual((found["status"], found["indistinct"]), ("same", False), found)
        self.assertEqual(len(found["large"]), 1)  # 정답 풀이는 제한 안에 통과한다


class CasegenUnchanged(unittest.TestCase):
    def test_builtin_random_stream_is_pinned(self):
        """기본 문제의 난수와 효율성 입력은 이 변경 앞과 같다."""
        stream = casegen.Rng(casegen.seed("bfs_1_warehouse_robot", 1))
        self.assertEqual([stream.next() for _ in range(3)], [13334992454924993656, 6563514008000547736, 13530987103319002640])
        source = (HERE / "problems/bfs/1_warehouse_robot/gen.py").read_text(encoding="utf-8")
        big = [casegen.large_args("bfs_1_warehouse_robot", source, n) for n in range(2)]
        self.assertEqual(hashlib.sha256(json.dumps(big).encode()).hexdigest(), "6cd383bacab56a2c5124c6a78958a3b025ba93914e026cac60ee81fb41c5f576")


if __name__ == "__main__":
    unittest.main()
