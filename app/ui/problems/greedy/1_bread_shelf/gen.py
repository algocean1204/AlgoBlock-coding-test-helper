LARGE = 1


def shop(rng, n, high, fresh_high):
    """n일 동안의 굽기·손님 수(0 ~ high)와 fresh(1 ~ fresh_high)."""
    baked = [rng.randint(0, high) if rng.chance(2, 3) else 0 for _ in range(n)]
    want = [rng.randint(0, high) for _ in range(n)]
    return [baked, want, rng.randint(1, fresh_high)]


def valid(baked, want, fresh):
    return (1 <= len(baked) == len(want) <= 100_000 and all(0 <= x <= 1_000 for x in baked + want)
            and 1 <= fresh <= 100_000)


def small(rng):
    cases = [
        [[0], [0], 1],
        [[5], [3], 1],
        [[3], [5], 100000],
        [[2, 0], [0, 2], 1],             # 하루만 팔 수 있다: 다음 날에는 버린다
        [[2, 0], [0, 2], 2],             # 이틀이면 판다
        [[3, 3], [1, 4], 2],             # 오래된 빵부터: 1일에 0일 빵 2개
        [[5, 5, 0], [1, 1, 8], 2],       # 새 빵부터 팔면 손해
        [[0, 0, 4], [3, 3, 3], 5],       # 빵이 없는 날 손님은 돌아간다
        [[1, 1, 1, 1, 1], [0, 0, 0, 0, 5], 1],
        [[1, 1, 1, 1, 1], [0, 0, 0, 0, 5], 3],
        [[9] * 10, [9] * 10, 3],
        [[4, 0, 0, 0, 4, 0], [0, 1, 1, 1, 0, 6], 3],
        [[6, 2, 0, 3], [2, 3, 4, 1], 2],
    ]
    while len(cases) < 18:
        case = shop(rng, rng.randint(5, 12), rng.choice([3, 6]), rng.choice([1, 2, 4, 15]))
        if case not in cases:
            cases.append(case)
    return cases


def medium(rng):
    # 원소의 최댓값(1,000)이 쓰이는 크기: brute.py로는 짝짓기가 너무 많다
    return [
        [[1000] * 10, [1000] * 10, 3],
        [[1000, 0, 0, 0], [0, 400, 400, 400], 3],     # 3일에는 0일 빵을 팔 수 없다: 800
        [[1000, 1000, 1000], [0, 0, 1000], 1],        # 1일만 팔 수 있어 그날 손님 수만큼만: 1000
    ]


def random_small(rng):
    return shop(rng, rng.randint(1, 6), rng.choice([2, 3]), rng.choice([1, 2, 3, 7]))


def large(rng, index):
    # 날마다 1,000개를 굽고 1,000명이 와서 그날까지 앞의 빵은 모두 다 팔린 상태다: 느린 풀이는 다 팔린 날을 매번 다시 지난다
    n = 100_000
    return [[1_000] * n, [1_000] * n, 100_000]
