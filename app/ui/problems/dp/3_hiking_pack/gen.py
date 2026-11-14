LARGE = 2


def pack(rng, n, heavy, high, room):
    """물건 n개(무게 1 ~ heavy, 쓸모 1 ~ high)와 무게 상한(무게 합의 room% 안팎)."""
    items = [[rng.randint(1, heavy), rng.randint(1, high)] for _ in range(n)]
    capacity = max(1, sum(weight for weight, _ in items) * room // 100)
    return [items, min(capacity, 10_000)]


def small(rng):
    cases = [
        [[[1, 1]], 1],
        [[[2, 5]], 1],  # 넣을 수 있는 것이 없다
        [[[10000, 10000]], 10000],  # 가장 큰 값, 꽉 채운다
        [[[1, 2], [1, 3], [1, 4]], 2],
        [[[5, 10], [4, 7], [4, 7]], 8],  # 무게당 쓸모가 큰 5를 먼저 넣으면 손해
        [[[6, 10], [3, 6], [3, 6]], 6],  # 쓸모가 큰 10을 먼저 넣으면 손해
        [[[3, 4], [3, 5]], 6],  # 꽉 채워야 한다
        [[[2, 3], [4, 7]], 5],  # 무게 5를 정확히 만들 수 없다
        [[[1, 10000]], 10000],  # 한 번만 넣을 수 있다
        [[[7, 7], [8, 8], [9, 9]], 6],
        [[[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]], 15],  # 모두 넣는다
        [[[4, 9], [4, 9], [4, 9], [4, 9]], 13],
    ]
    for _ in range(6):
        cases.append(pack(rng, rng.randint(6, 14), rng.choice([10, 50]), rng.choice([20, 10000]), rng.randint(20, 70)))
    return cases


def random_small(rng):
    n = rng.randint(1, 8)
    return [[[rng.randint(1, 8), rng.randint(1, 10)] for _ in range(n)], rng.randint(1, 20)]


def valid(items, capacity):
    return (1 <= len(items) <= 100 and 1 <= capacity <= 10_000
            and all(len(item) == 2 and 1 <= item[0] <= 10_000 and 1 <= item[1] <= 10_000 for item in items))


def large(rng, index):
    # 물건 100개, 무게 상한 10,000. 무게 합이 상한을 조금 넘어 넣는 방법이 아주 많다
    if index == 0:
        items = [[rng.randint(1, 250), rng.randint(1, 10000)] for _ in range(100)]
    else:
        items = []
        for _ in range(100):  # 무게와 쓸모가 비슷해 탐욕이 잘 틀리는 모양
            weight = rng.randint(80, 200)
            items.append([weight, weight * 40 + rng.randint(0, 400)])
    return [items, 10_000]
