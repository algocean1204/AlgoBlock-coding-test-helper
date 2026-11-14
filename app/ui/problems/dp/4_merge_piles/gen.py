LARGE = 2


def small(rng):
    cases = [
        [[5]],  # 한 더미
        [[1, 1]],
        [[5000, 5000]],
        [[3, 3, 3]],
        [[1, 2, 3, 4]],
        [[4, 3, 2, 1]],
        [[2, 4, 1, 4]],  # 이웃 탐욕도, 힙 탐욕도 틀린다
        [[1, 9, 1, 9, 1]],
        [[9, 6, 9, 8, 9]],
        [[2, 6, 9, 4, 9]],
        [[1, 5000, 1, 5000]],
        [[5000] * 8],  # 가장 큰 값
    ]
    for _ in range(6):
        n = rng.randint(5, 8)
        high = rng.choice([9, 5000])
        cases.append([[rng.randint(1, high) for _ in range(n)]])
    return cases


def random_small(rng):
    n = rng.randint(1, 7)
    return [[rng.randint(1, 9) for _ in range(n)]]


def valid(piles):
    return 1 <= len(piles) <= 200 and all(1 <= x <= 5_000 for x in piles)


def large(rng, index):
    if index == 0:
        return [[rng.randint(1, 5000) for _ in range(200)]]
    return [[rng.randint(4500, 5000) if i % 3 else rng.randint(1, 100) for i in range(200)]]  # 큰 더미 사이에 작은 더미
