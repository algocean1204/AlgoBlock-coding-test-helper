LARGE = 2


def connected_roads(rng, towns, extra, high):
    """towns를 모두 잇는 무작위 나무에 무작위 길 extra개를 더해 섞는다. 비용은 1~high."""
    order = rng.shuffle(list(towns))
    roads = []
    for i in range(1, len(order)):
        j = rng.randint(0, i - 1)
        roads.append([order[i], order[j], rng.randint(1, high)])
    for _ in range(extra):
        i, j = rng.distinct(0, len(order) - 1, 2)
        roads.append([order[i], order[j], rng.randint(1, high)])
    return rng.shuffle(roads)


def valid(n, roads):
    return 1 <= n <= 50_000 and len(roads) <= 100_000 and all(1 <= a <= n and 1 <= b <= n and a != b and 1 <= cost <= 10_000 for a, b, cost in roads)


def any_roads(rng, n, count, high):
    return [rng.distinct(1, n, 2) + [rng.randint(1, high)] for _ in range(count)]


def small(rng):
    cases = [
        [1, []],
        [2, []],
        [2, [[1, 2, 10000]]],
        [2, [[2, 1, 5], [1, 2, 3], [1, 2, 9]]],
        [4, [[1, 2, 1], [3, 4, 1], [2, 3, 10]]],  # 마을마다 가장 싼 길만 고르면 두 묶음으로 끊긴다
        [4, [[1, 2, 9], [2, 3, 9], [3, 4, 9], [1, 4, 1], [1, 3, 1]]],  # 주어진 순서대로 고르면 비싼 길을 먼저 고른다
        [4, [[1, 2, 1], [3, 2, 2], [1, 3, 3], [3, 4, 4]]],  # 대표가 아닌 번호를 바로 이으면 1번이 떨어져 나간다
        [6, [[1, 2, 3], [2, 3, 4], [1, 3, 1], [4, 5, 2], [5, 6, 2], [4, 6, 7]]],  # 두 묶음으로 나뉘어 있다
        [5, [[a, b, 7] for a in range(1, 6) for b in range(a + 1, 6)]],
        [6, [[1, k, k] for k in range(2, 7)] + [[k, k + 1, 10000] for k in range(2, 6)]],
        [7, [[k, k + 1, 100 - k] for k in range(1, 7)]],
    ]
    for _ in range(5):
        n = rng.randint(5, 20)
        cases.append([n, connected_roads(rng, range(1, n + 1), rng.randint(0, 2 * n), rng.choice([5, 100, 10000]))])
    for _ in range(2):
        n = rng.randint(5, 12)
        cases.append([n, any_roads(rng, n, rng.randint(n - 2, n + 3), 20)])
    return cases


def random_small(rng):
    n = rng.randint(1, 6)
    if n == 1:
        return [1, []]
    if rng.chance(2, 3):
        return [n, connected_roads(rng, range(1, n + 1), rng.randint(0, 5), 5)]
    return [n, any_roads(rng, n, rng.randint(0, 7), 5)]


def large(rng, index):
    n = 50_000
    if index == 0:  # 모두 이을 수 있다. 싼 길로 큰 묶음이 생긴 뒤에도 고리를 만드는 길이 5만 개 남는다
        return [n, connected_roads(rng, range(1, n + 1), 100_000 - (n - 1), 10_000)]
    half = n // 2  # 두 묶음으로 나뉘어 끝내 이을 수 없다
    roads = connected_roads(rng, range(1, half + 1), 25_001, 10_000) + connected_roads(rng, range(half + 1, n + 1), 25_001, 10_000)
    return [n, rng.shuffle(roads)]
