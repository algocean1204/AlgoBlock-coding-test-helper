LARGE = 2


def pair(rng, low, high):
    a, b = rng.randint(low, high), rng.randint(low, high)
    return [min(a, b), max(a, b)]


def small(rng):
    cases = [
        [[5], [[5, 5]]],  # 매물 하나, 딱 그 가격
        [[5], [[1, 4], [6, 10], [1, 1000000000]]],  # 앞·뒤·전체
        [[4, 4, 4, 4], [[4, 4], [1, 3], [5, 9], [3, 4], [4, 5]]],  # 모두 같은 가격
        [[1, 2, 3, 4, 5], [[1, 5], [2, 4], [5, 5], [1, 1], [6, 7]]],  # 이미 정렬됨
        [[9, 7, 5, 3, 1], [[2, 8], [1, 9], [3, 3], [10, 20]]],  # 거꾸로 정렬됨
        [[1000000000, 1, 1000000000, 500000000], [[1000000000, 1000000000], [1, 1000000000], [2, 999999999]]],
        [[30, 10, 20, 10, 30, 20, 10], [[10, 10], [10, 20], [20, 30], [11, 19], [31, 40]]],
    ]
    for _ in range(8):
        prices = [rng.randint(1, 60) for _ in range(rng.randint(1, 80))]
        cases.append([prices, [pair(rng, 1, 65) for _ in range(rng.randint(1, 20))]])
    return cases


def valid(prices, ranges):
    return (1 <= len(prices) <= 100_000 and all(1 <= p <= 1_000_000_000 for p in prices) and 1 <= len(ranges) <= 50_000
            and all(len(r) == 2 and 1 <= r[0] <= r[1] <= 1_000_000_000 for r in ranges))


def random_small(rng):
    prices = [rng.randint(1, 12) for _ in range(rng.randint(1, 10))]
    return [prices, [pair(rng, 1, 13) for _ in range(rng.randint(1, 5))]]


def large(rng, index):
    pool = [rng.randint(1, 1_000_000_000) for _ in range(20_000)]
    prices = [rng.choice(pool) if rng.chance(1, 2) else rng.randint(1, 1_000_000_000) for _ in range(100_000)]  # 같은 가격이 여럿
    if index == 0:  # 아무 가격대
        ranges = [pair(rng, 1, 1_000_000_000) for _ in range(50_000)]
    else:  # 넓은 가격대: 앞에서부터 걸으면 거의 끝까지 간다
        ranges = [[rng.randint(1, 100_000_000), rng.randint(900_000_000, 1_000_000_000)] for _ in range(50_000)]
    return [prices, ranges]
