LARGE = 2
TOP = 100_000_000


def road(rng, u, v, low, high):
    slow = rng.randint(low, high)
    return [u, v, slow, rng.randint(max(1, slow // 4), slow)]


def valid(n, roads, farms, market):
    if not (2 <= n <= 20_000 and 1 <= len(roads) <= 60_000 and 1 <= len(farms) <= 5):
        return False
    if any(len(r) != 4 or not (1 <= r[0] <= n and 1 <= r[1] <= n and r[0] != r[1] and 1 <= r[3] <= r[2] <= TOP) for r in roads):
        return False
    return len(set(farms)) == len(farms) and all(1 <= f <= n for f in farms) and 1 <= market <= n


def random_roads(rng, n, count, low, high, loop):
    """한 방향 도로 count개. loop이면 모든 마을을 한 바퀴 도는 길을 먼저 깔아 어디서든 어디로든 갈 수 있게 한다."""
    order = rng.shuffle(list(range(1, n + 1)))
    roads = [road(rng, order[i], order[(i + 1) % n], low, high) for i in range(n)] if loop else []
    while len(roads) < count:
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v:
            roads.append(road(rng, u, v, low, high))
    return rng.shuffle(roads)


def with_ends(rng, n, roads, farm_count):
    return [n, roads, rng.sample(range(1, n + 1), farm_count), rng.randint(1, n)]


def arms(rng, n, count, low, high, farm_count):
    """농장마다 긴 팔이 가운데 마을로 모이고, 가운데에서 시장까지 또 긴 팔이 있다. 팔 안에는 앞으로 건너뛰는 지름길이 섞인다."""
    labels = rng.shuffle(list(range(1, n + 1)))
    size = n // (farm_count + 1)
    chains = [labels[i * size:(i + 1) * size] for i in range(farm_count)] + [labels[farm_count * size:]]
    hub = chains[-1][0]
    for chain in chains[:-1]:
        chain.append(hub)
    roads = [road(rng, chain[i], chain[i + 1], low, high) for chain in chains for i in range(len(chain) - 1)]
    while len(roads) < count:
        chain = rng.choice(chains)
        i = rng.randint(0, len(chain) - 2)
        roads.append(road(rng, chain[i], chain[min(len(chain) - 1, i + rng.randint(1, 3))], low, high))
    return [n, rng.shuffle(roads), [chain[0] for chain in chains[:-1]], chains[-1][-1]]


def small(rng):
    cases = [
        [2, [[1, 2, 5, 3]], [1], 2],  # 가장 작은 입력: 농장 하나
        [2, [[1, 2, 5, 3]], [2], 1],  # 시장으로 가는 길이 없다
        [2, [[2, 1, 7, 7]], [1], 1],  # 농장이 곧 시장
        [3, [[1, 3, 4, 1], [2, 3, 4, 1], [3, 1, 4, 4]], [1, 2], 3],
        [3, [[1, 2, 10, 1], [2, 3, 10, 1], [1, 3, 15, 15]], [1], 3],  # 일찍 큰 트럭으로 바꾸는 편이 빠르다
        [4, [[1, 2, 3, 3], [3, 2, 9, 9], [2, 4, 1, 1], [4, 1, 1, 1]], [1, 3], 4],  # 늦은 트럭을 기다린다(합이 아니다)
        [4, [[1, 2, 2, 1], [2, 3, 2, 1], [3, 4, 2, 1], [4, 1, 2, 1]], [1, 3], 2],  # 한 바퀴 도는 길
        [4, [[2, 1, 1, 1], [3, 1, 1, 1], [1, 4, 1, 1]], [2, 3], 1],  # 시장으로 모이는 길만 있다
        [4, [[1, 2, 1, 1], [3, 2, 1, 1], [4, 2, 1, 1]], [1, 3], 4],  # 거꾸로 지나야만 시장에 갈 수 있다
        [5, [[1, 3, 4, 2], [2, 3, 6, 3], [3, 5, 10, 2], [1, 5, 15, 9], [2, 4, 3, 1], [4, 5, 7, 6], [5, 1, 1, 1]], [1, 2, 4], 5],
        [5, [[1, 2, 1, 1], [1, 2, 9, 1], [2, 3, 5, 5], [2, 3, 6, 2], [4, 3, 3, 3], [3, 5, 4, 4]], [1, 4], 5],  # 같은 방향의 도로가 여럿
        [26, [[i, i + 1, TOP, TOP] for i in range(1, 26)] + [[26, 1, 1, 1]], [1, 2, 3, 4, 5], 26],  # 답이 int를 넘는다(25억)
        [12, [[i, i + 1, TOP, TOP // 2] for i in range(1, 12)], [1], 12],  # 농장에서 바로 큰 트럭으로 옮겨 싣는 편이 빠르다
    ]
    cases.append(arms(rng, 21, 30, 1, 20, 3))
    cases.append(arms(rng, 30, 40, TOP // 2, TOP, 4))
    for n, count, high, loop, farm in ((6, 10, 9, True, 2), (8, 12, 20, False, 3), (12, 25, 9, True, 4), (16, 30, TOP, True, 5), (20, 30, 50, False, 2)):
        cases.append(with_ends(rng, n, random_roads(rng, n, count, 1, high, loop), farm))
    return cases


def random_small(rng):
    n = rng.randint(2, 6)
    return with_ends(rng, n, random_roads(rng, n, rng.randint(1, 3 * n), 1, 9, rng.chance(1, 2)), rng.randint(1, min(3, n)))


def large(rng, index):
    if index == 0:  # 아무렇게나 이어진 마을 2만 곳, 어디서든 어디로든 갈 수 있다
        return with_ends(rng, 20_000, random_roads(rng, 20_000, 60_000, 1, TOP, True), 5)
    return arms(rng, 20_000, 60_000, TOP // 2, TOP, 5)  # 팔이 길어 시간 합이 int를 넘는다
