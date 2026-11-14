LARGE = 2
N, ROADS, TOLL, PASSES = 8_000, 60_000, 20_000, 12


def valid(n, roads, k):
    if not (2 <= n <= N and 1 <= len(roads) <= ROADS and 0 <= k <= PASSES):
        return False
    return all(1 <= u <= n and 1 <= v <= n and u != v and 1 <= toll <= TOLL for u, v, toll in roads)


def random_roads(rng, n, count, high):
    """아무 두 도시나 잇는 도로 count개. 이어지지 않은 도시가 생길 수 있다."""
    roads = []
    while len(roads) < count:
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v:
            roads.append([u, v, rng.randint(1, high)])
    return roads


def strip(rng, cities, count, high):
    """cities를 한 줄로 늘어놓고 이웃한 도시끼리 잇고, 다섯 칸 안쪽의 도시끼리 도로를 덧붙인다.
    맨 앞 도시에서 맨 뒤 도시까지 도로를 수천 개 지나야 해서 통행권 k장이 답을 0으로 만들지 못한다."""
    roads = [[cities[i], cities[i + 1], rng.randint(1, high)] for i in range(len(cities) - 1)]
    while len(roads) < count:
        i = rng.randint(0, len(cities) - 2)
        roads.append([cities[i], cities[min(len(cities) - 1, i + rng.randint(1, 5))], rng.randint(1, high)])
    return roads


def mixed(rng, roads):
    for road in roads:
        if rng.chance(1, 2):
            road[0], road[1] = road[1], road[0]
    return rng.shuffle(roads)


def small(rng):
    cases = [
        [2, [[1, 2, 5]], 0],
        [2, [[1, 2, 5]], 1],
        [2, [[2, 1, 5]], 12],  # 통행권이 도로 수보다 많다
        [3, [[1, 2, 40], [2, 3, 30]], 2],  # 두 도로가 이어져 있어 한 장만 쓸 수 있다
        [4, [[1, 2, 1000], [2, 4, 1000], [2, 3, 1]], 2],  # 2번에서 3번에 다녀오면 통행권을 다시 쓸 수 있다
        [4, [[1, 2, 1000], [2, 4, 1000], [2, 3, 1]], 1],
        [4, [[1, 2, 1], [2, 3, 1], [3, 4, 1], [1, 4, 50]], 1],  # 통행권을 쓰면 비싼 지름길이 가장 싸다
        [4, [[1, 2, 4], [2, 4, 4], [1, 3, 1], [3, 4, 9], [2, 3, 20000]], 1],  # 가장 비싼 도로는 쓸모가 없다
        [3, [[1, 2, 10], [1, 2, 2], [2, 3, 10], [2, 1, 1]], 1],  # 같은 두 도시 사이 도로 셋
        [3, [[1, 2, 2], [1, 2, 9], [2, 3, 5], [3, 2, 8]], 1],  # 같은 두 도시 사이 도로에서 싼 쪽이 먼저 적혀 있다
        [5, [[1, 2, 3], [2, 3, 3], [4, 5, 3]], 3],  # 갈 수 없다
        [6, [[1, 2, 1], [2, 6, 100], [1, 3, 30], [3, 4, 30], [4, 6, 30], [3, 5, 1], [5, 4, 1]], 1],  # 통행료만 보면 1-3-5-4-6이 가장 싸다
        [13, [[i, i + 1, 10 * i] for i in range(1, 13)], 12],  # 한 줄 도로 12개: 한 칸 걸러 쓴다
        [6, [[1, 2, 7], [2, 3, 9], [3, 4, 9], [4, 5, 7], [5, 6, 9], [2, 4, 18]], 3],  # 같은 값으로 닿아도 앞에 통행권을 썼는지가 다르다
    ]
    for n, count, high, k in ((6, 8, 9, 1), (8, 11, 20, 2), (9, 12, TOLL, 3), (10, 13, 9, 4)):
        cases.append([n, mixed(rng, random_roads(rng, n, count, high)), k])
    cities = rng.shuffle(list(range(2, 11)))
    cases.append([11, mixed(rng, strip(rng, [1] + cities + [11], 16, 100)), 3])
    return cases


def random_small(rng):
    n = rng.randint(3, 7)
    if rng.chance(1, 5):  # 이어지지 않았을 수 있는 성긴 지도
        return [n, random_roads(rng, n, rng.randint(1, n), 9), rng.randint(0, 3)]
    # 1번에서 n번까지 한 줄로 잇고 도로 몇 개를 덧붙인다(길이 짧아 답이 0으로 쏠리지 않게)
    cities = [1] + rng.shuffle(list(range(2, n))) + [n]
    roads = [[cities[i], cities[i + 1], rng.randint(1, 9)] for i in range(n - 1)] + random_roads(rng, n, rng.randint(0, 3), 9)
    return [n, mixed(rng, roads), rng.randint(0, 3)]


def large(rng, index):
    middle = rng.shuffle(list(range(2, N)))
    if index == 0:  # 1번이 한쪽 끝, n번이 반대쪽 끝: n번이 가장 늦게 확정된다
        return [N, mixed(rng, strip(rng, [1] + middle + [N], ROADS, TOLL)), PASSES]
    # n번은 따로 떨어진 작은 무리에 있다: 1번에서 닿는 상태를 모두 본 뒤에야 -1을 안다
    roads = strip(rng, [1] + middle[:-1], ROADS - 1, TOLL) + [[middle[-1], N, rng.randint(1, TOLL)]]
    return [N, mixed(rng, roads), PASSES]
