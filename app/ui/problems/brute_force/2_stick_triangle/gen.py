LARGE = 0


def small(rng):
    cases = [
        [[1, 2, 3]],                  # 가장 긴 것이 나머지 합과 같다
        [[1, 1, 1]],                  # 가장 작은 입력
        [[10, 3, 4]],                 # 가장 긴 막대가 맨 앞에 있다
        [[1500, 1500, 1]],            # 가장 큰 길이, 아슬아슬하게 된다
        [[1500, 1499, 1]],             # 가장 큰 길이, 아슬아슬하게 안 된다
        [[1500] * 100],               # 모두 같고 가장 많다: 161,700
        [[2, 2, 2, 2, 4]],
        [[7, 7, 3, 3, 1, 1]],
        [[1, 1, 2, 2, 3, 3, 4, 4]],
        [list(range(1, 101))],        # 오름차순
        [list(range(100, 0, -1))],    # 내림차순
        [[1, 2, 4, 8, 16, 32, 64]],   # 어떤 세 개도 안 된다
    ]
    for _ in range(3):
        cases.append([[rng.randint(1, 10) for _ in range(rng.randint(10, 40))]])
    for _ in range(3):
        cases.append([[rng.randint(1, 1500) for _ in range(rng.randint(3, 100))]])
    return cases


def valid(sticks):
    return 3 <= len(sticks) <= 100 and all(1 <= length <= 1500 for length in sticks)


def random_small(rng):
    return [[rng.randint(1, 6) for _ in range(rng.randint(3, 8))]]
