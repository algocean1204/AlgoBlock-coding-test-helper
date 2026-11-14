LARGE = 2


def small(rng):
    cases = [
        [[0]],
        [[10000]],
        [[5, 1]],  # 첫날만: 둘째 칸 시작값 실수
        [[1, 5]],
        [[0, 0, 0, 0]],
        [[7, 7, 7, 7, 7]],
        [[6, 9, 6, 1]],  # 가장 큰 9를 먼저 고르면 손해
        [[9, 1, 0, 5]],  # 첫날 + 넷째 날
        [[1, 9, 1, 1, 9, 1]],  # 이틀 연달아 쉬어야 한다
        [[10, 1, 1, 10, 1, 1, 10]],
        [[4, 10, 4]],
        [[8, 1, 1, 8, 1, 1, 8, 1]],  # 마지막 날은 쉰다
        [[10000] * 18],
    ]
    for _ in range(5):
        n = rng.randint(6, 18)
        high = rng.choice([9, 100, 10000])
        cases.append([[rng.randint(0, high) for _ in range(n)]])
    return cases


def random_small(rng):
    n = rng.randint(1, 10)
    return [[rng.randint(0, 9) for _ in range(n)]]


def valid(pay):
    return 1 <= len(pay) <= 100_000 and all(0 <= x <= 10_000 for x in pay)


def large(rng, index):
    n = 100_000
    if index == 0:
        return [[rng.randint(0, 10000) for _ in range(n)]]
    # 큰 값이 두세 칸 간격으로 섞여 있어 하루씩 건너뛰기로는 안 되는 모양
    return [[rng.randint(9000, 10000) if rng.chance(1, 3) else rng.randint(0, 3000) for _ in range(n)]]
