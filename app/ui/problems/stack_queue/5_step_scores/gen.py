LARGE = 3


def valid(scores, jump):
    return 1 <= len(scores) <= 200_000 and all(-100_000 <= score <= 100_000 for score in scores) and 1 <= jump <= len(scores)


def small(rng):
    cases = [
        [[5], 1],
        [[-100000], 1],
        [[3, -7], 1],
        [[1, -100, 2], 1],                         # 뛸 수 있는 거리가 1이면 모두 밟는다
        [[1, -100, 2], 2],
        [[-5, -1, -9, -2, -8, -3], 2],             # 모두 음수
        [[0, 0, 0, 0], 4],
        [[2, -1, -1, -1, -1, 3], 4],               # 음수 넷을 한 번에 건너뛴다
        [[2, -1, -1, -1, -1, 3], 3],               # 음수 하나는 밟아야 한다
        [[1, 9, -50, -50, 8, -50, -50, 1], 3],     # 음수 둘씩은 건너뛸 수 있다
        [[-9, 6, -1, -9, -2, -2, -2, -4, 6], 3],   # 닿는 돌 가운데 가장 큰 돌로 뛰는 욕심이 틀린다
        [[4, -3, 7, -3, -3, 7, -3, 4], 2],
        [[100000] * 50, 50],
        [[-100000] * 50, 1],
    ]
    cases.append([[rng.randint(-100000, 100000) for _ in range(150)], 7])
    cases.append([[rng.randint(-20, 5) for _ in range(150)], 4])
    while len(cases) < 19:
        n = rng.randint(6, 40)
        case = [[rng.randint(-9, 9) for _ in range(n)], rng.randint(1, min(n, 6))]
        if case not in cases:
            cases.append(case)
    return cases


def random_small(rng):
    n = rng.randint(1, 10)
    return [[rng.randint(-9, 9) for _ in range(n)], rng.randint(1, n)]


def large(rng, index):
    n = 200_000
    if index == 0:  # 점수가 고루 섞이고 jump가 크다: 돌마다 앞을 다시 훑으면 n × jump번
        return [[rng.randint(-100_000, 100_000) for _ in range(n)], 100_000]
    if index == 1:  # 모두 가장 큰 점수: 답이 200억이라 int를 넘는다
        return [[100_000] * n, n]
    # 돌마다 최고 점수가 줄어들기만 한다: 범위의 가장 큰 값이 매번 범위를 벗어난다
    jump = 100_000
    return [[0] + [-i for i in range(1, jump + 1)] + [-jump] * (n - 1 - jump), jump]
