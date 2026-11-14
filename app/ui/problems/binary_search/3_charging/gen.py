LARGE = 2


def small(rng):
    cases = [
        [1, [1]],  # 가장 작은 입력
        [1, [100000]],  # 가장 느린 충전기 하나
        [10, [1]],
        [5, [3, 3, 3]],  # 모두 같은 시간, n이 충전기 수로 나누어떨어지지 않는다
        [7, [2, 3, 7]],
        [3, [100000, 1]],  # 느린 충전기는 쓰지 않는 편이 빠르다
        [2, [9, 4, 6, 8, 3]],  # 충전기가 킥보드보다 많다
        [13, [5, 5, 5, 5]],
        [60, [1000, 999]],
        [200, [7, 11, 13, 17]],
    ]
    for _ in range(6):
        chargers = [rng.randint(1, 50) for _ in range(rng.randint(1, 30))]
        cases.append([rng.randint(1, 200), chargers])
    return cases


def medium(rng):  # 답이나 판정 중 개수 합이 int를 넘는다: 정의 그대로 풀이로는 못 돌린다
    return [
        [500000000, [100000]],  # 답 = n × 100000
        [21475, [100000]],  # 답 2,147,500,000: int 최댓값을 살짝 넘는다
        [500000000, [2] * 300],  # 답은 int 안이지만 판정 중 대수의 합이 수백억이 된다
        [500000000, [1] * 10],  # 답 = n ÷ 10. 판정 중 대수의 합이 25억을 넘는다
        [500000000, [99999, 100000]],
    ]


def valid(n, chargers):
    return 1 <= n <= 500_000_000 and 1 <= len(chargers) <= 50_000 and all(1 <= c <= 100_000 for c in chargers)


def random_small(rng):
    return [rng.randint(1, 12), [rng.randint(1, 9) for _ in range(rng.randint(1, 4))]]


def large(rng, index):
    n = 500_000_000
    if index == 0:  # 충전기가 가장 많다
        return [n, [rng.randint(1, 100_000) for _ in range(50_000)]]
    return [n, [rng.randint(90_000, 100_000) for _ in range(7)]]  # 느린 충전기 몇 대: 답이 int를 넘는다
