LARGE = 3
TOP = 1_000_000_000


def small(rng):
    cases = [
        [[0]],  # 가장 작은 입력, 답 0
        [[1]],  # 값이 딱 x와 같다: '이상'을 '초과'로 읽으면 틀린다
        [[TOP]],  # 가장 큰 값이어도 회원이 1명이면 답은 1
        [[2, 2]],
        [[0, 0, 0, 5]],
        [[1, 1, 1, 1]],
        [[5, 4, 3, 2, 1]],  # 이미 큰 순서
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],  # 작은 순서: 정렬하지 않고 훑으면 틀린다
        [[0, 9, 9, 9, 9, 9, 9, 9, 9, 9]],  # 맨 앞만 작다
        [[1000] * 150],  # 모든 값이 회원 수보다 크다: 답은 회원 수
    ]
    big = [rng.randint(20, TOP) for _ in range(20)]
    low = [rng.randint(0, 19) for _ in range(20)]
    cases.append([rng.shuffle(big + low)])  # 큰 값 절반, 작은 값 절반
    for _ in range(6):
        n = rng.randint(5, 100)
        cases.append([[rng.randint(0, 2 * n) for _ in range(n)]])
    return cases


def random_small(rng):
    return [[rng.randint(0, 12) for _ in range(rng.randint(1, 10))]]


def large(rng, index):
    n = 200_000
    if index == 0:  # 답이 회원 수의 절반: x를 위로 올려도, 아래로 내려도 10만 번씩 전체를 센다
        half = n // 2
        values = [rng.randint(half, TOP) for _ in range(half)] + [rng.randint(0, half - 1) for _ in range(half)]
        return [rng.shuffle(values)]
    if index == 1:  # 모든 값이 회원 수 이상: 답이 회원 수(가장 큰 답)
        return [[rng.randint(n, TOP) for _ in range(n)]]
    return [[rng.randint(0, 1000) for _ in range(n)]]  # 답이 작다: 회원 수부터 내려오면 오래 걸린다
