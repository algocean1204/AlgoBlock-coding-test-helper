"""기본 문제의 채점 입력을 만드는 난수. 파이썬 버전이 달라도 같은 씨앗이면 같은 값이 나와야 해서 random 모듈을 쓰지 않는다.

큰 입력(효율성 케이스)은 저장하지 않고 채점할 때마다 이 난수로 다시 만든다. 기대 결과는 만들 때 구해 저장해 두므로,
여기 계산이 한 글자라도 바뀌면 맞는 풀이가 틀렸다고 나온다. 고치지 않는다(test_server.py가 저장된 기대 결과와 대조한다).
"""

import math
import zlib

MASK = (1 << 64) - 1
# 효율성 케이스의 언어별 제한 시간(초). 느린 풀이를 파이썬에서 걸러 내는 크기로 만든 입력이라, 빠른 언어는 제한을 짧게 잡아야 같은 풀이가 걸린다.
# 잰 값: 느린 풀이를 C++로 옮기면 여러 문제에서 2~4초에 끝났다(제한 4초일 때 통과). 정답 풀이는 C++·Go·Rust 0.6초, Java·Kotlin·JavaScript 0.6초 안쪽이었다.
LIMIT = {"python": 10, "javascript": 4, "java": 4, "kotlin": 4, "go": 2, "cpp": 2, "rust": 2}
# 기본 문제는 위 표를 상한으로, 문제마다·언어마다 정답 풀이가 걸린 시간에서 제한을 정한다(문제 폴더의 limits.json. problemkit.check가 잰다)
FACTOR = 8  # 정답과 같은 방법이지만 덜 다듬은 풀이를 떨어뜨리지 않을 만큼의 배수
FLOOR = 1.0  # 프로세스가 뜨는 시간과 기계 차이를 견디는 가장 짧은 제한(초)
STEP = 0.5  # 제한은 이 단위(초)로 올린다(다시 잴 때마다 값이 조금씩 흔들리지 않게)


def limit_of(language: str, seconds: float) -> float:
    """정답 풀이가 가장 오래 걸린 효율성 케이스의 시간(초)에서 그 언어의 제한(초)."""
    steps = math.ceil(round(seconds * FACTOR / STEP, 6))  # round: 1.5000000001 같은 실수 오차로 한 칸 더 올리지 않게
    return float(min(LIMIT[language], max(FLOOR, steps * STEP)))


def seed(problem_id: str, salt: int = 0) -> int:
    """문제마다 정해진 씨앗. salt로 쓰임새를 나눈다(1 정확성, 100+번호 효율성, 1000+번호 무작위 대조)."""
    return zlib.crc32(problem_id.encode()) * 1000 + salt


def large_args(problem_id: str, source: str, index: int) -> list:
    """효율성 케이스 하나의 인자를 gen.py 소스(source)로 만든다. 채점할 때마다 같은 값이 나온다. 소스는 우리가 써서 실은 것이다."""
    scope = {"__name__": "gen"}
    exec(compile(source, f"{problem_id}/gen.py", "exec"), scope)
    return scope["large"](Rng(seed(problem_id, 100 + index)), index)


class Rng:
    """xorshift64*. 정수만 다룬다(실수는 쓰지 않는다)."""

    def __init__(self, seed: int):
        self.state = ((seed + 1) * 0x9E3779B97F4A7C15) & MASK or 1

    def next(self) -> int:
        x = self.state
        x ^= x >> 12
        x ^= (x << 25) & MASK
        x ^= x >> 27
        self.state = x
        return (x * 0x2545F4914F6CDD1D) & MASK

    def randint(self, low: int, high: int) -> int:
        """low 이상 high 이하."""
        return low + self.next() % (high - low + 1)

    def chance(self, numerator: int, denominator: int) -> bool:
        """numerator/denominator의 확률로 참."""
        return self.next() % denominator < numerator

    def choice(self, items):
        return items[self.next() % len(items)]

    def shuffle(self, items: list) -> list:
        """제자리에서 섞고 그 목록을 돌려준다."""
        for i in range(len(items) - 1, 0, -1):
            j = self.next() % (i + 1)
            items[i], items[j] = items[j], items[i]
        return items

    def sample(self, items, count: int) -> list:
        """겹치지 않게 count개."""
        return self.shuffle(list(items))[:count]

    def distinct(self, low: int, high: int, count: int) -> list:
        """low 이상 high 이하에서 서로 다른 정수 count개(범위가 아주 커도 된다)."""
        if high - low + 1 <= count * 3:
            return self.sample(range(low, high + 1), count)
        seen = set()
        while len(seen) < count:
            seen.add(self.randint(low, high))
        return self.shuffle(sorted(seen))

    def word(self, length: int, letters: str = "abcdefghijklmnopqrstuvwxyz") -> str:
        return "".join(letters[self.next() % len(letters)] for _ in range(length))


if __name__ == "__main__":  # 값이 바뀌지 않았는지 보는 자체 확인
    r = Rng(7)
    got = [r.randint(1, 100) for _ in range(5)] + [r.choice("abc"), r.shuffle([1, 2, 3, 4, 5]), r.distinct(1, 10**9, 3), r.word(6)]
    assert got == [20, 83, 20, 9, 32, "b", [1, 3, 5, 4, 2], [947912938, 650158419, 562784346], "xtrxaq"], got
    print("ok")
