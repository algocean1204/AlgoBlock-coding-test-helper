LARGE = 2


def valid(n, roads):
    if not (2 <= n <= 66_000 and n - 1 <= len(roads) <= 66_000):
        return False
    if any(not (1 <= a <= n and 1 <= b <= n and a != b and 1 <= time <= 9_000) for a, b, time in roads):
        return False
    near = [[] for _ in range(n + 1)]  # 1번 마을에서 모든 마을로 갈 수 있는가
    for a, b, _ in roads:
        near[a].append(b)
        near[b].append(a)
    seen = {1}
    stack = [1]
    while stack:
        for nxt in near[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == n


def connected(rng, n, count, low, high, reach=0):
    """1~n번 마을이 모두 이어진 길 count개.
    섞은 순서대로 마을마다 앞선 마을 하나와 이어 나무를 만들고(reach가 있으면 reach칸 앞까지만: 길고 가는 모양), 나머지 길은 덧붙인다."""
    order = [1] + rng.shuffle(list(range(2, n + 1)))
    roads = []
    for i in range(1, n):
        low_index = max(0, i - reach) if reach else 0
        roads.append([order[i], order[rng.randint(low_index, i - 1)], rng.randint(low, high)])
    while len(roads) < count:
        i = rng.randint(0, n - 1)
        j = min(n - 1, i + rng.randint(1, reach)) if reach else rng.randint(0, n - 1)
        if i != j:
            roads.append([order[i], order[j], rng.randint(low, high)])
    for road in roads:
        if rng.chance(1, 2):
            road[0], road[1] = road[1], road[0]
    return rng.shuffle(roads)


def with_copies(rng, roads, copies, low, high):
    """같은 두 마을을 잇는 길을 copies개 더 넣는다(시간은 새로 정한다)."""
    for _ in range(copies):
        a, b, _ = rng.choice(roads)
        roads.append([b, a, rng.randint(low, high)] if rng.chance(1, 2) else [a, b, rng.randint(low, high)])
    return rng.shuffle(roads)


def small(rng):
    cases = [
        [2, [[1, 2, 1]]],
        [2, [[2, 1, 9000]]],
        [2, [[1, 2, 5], [2, 1, 3], [1, 2, 8]]],  # 같은 두 마을 사이 길 셋, 가장 빠른 길이 가운데에 적혀 있다
        [3, [[1, 2, 1], [2, 3, 1], [1, 3, 2]]],  # 두 경로의 시간이 같다
        [4, [[1, 2, 10], [1, 3, 1], [3, 4, 1], [4, 2, 1]]],  # 먼저 닿은 길보다 돌아가는 길이 빠르다
        [5, [[5, 4, 2], [4, 3, 2], [3, 2, 2], [2, 1, 2]]],  # 길이 모두 거꾸로 적혀 있다
        [6, [[1, 2, 7], [1, 3, 7], [1, 4, 7], [1, 5, 7], [1, 6, 7]]],  # 별 모양
        [4, [[3, 1, 4], [1, 3, 9], [3, 2, 9], [2, 3, 1], [4, 2, 2], [2, 4, 6], [1, 4, 30]]],
        [6, [[1, 2, 9000], [1, 3, 1], [3, 4, 1], [4, 5, 1], [5, 6, 1], [6, 2, 1], [2, 6, 9]]],
    ]
    for n, count, high, copies in ((8, 10, 9, 3), (12, 16, 20, 4), (20, 30, 9000, 5), (30, 40, 50, 6), (40, 55, 9000, 6)):
        cases.append([n, with_copies(rng, connected(rng, n, count, 1, high), copies, 1, high)])
    cases.append([40, with_copies(rng, connected(rng, 40, 60, 1, 100, reach=3), 8, 1, 100)])  # 길고 가는 모양: 길 수가 많아도 빠른 길이 흔하다
    return cases


def random_small(rng):
    n = rng.randint(2, 7)
    roads = connected(rng, n, n - 1 + rng.randint(0, 5), 1, 9, reach=rng.choice([0, 2]))
    return [n, with_copies(rng, roads, rng.randint(0, 2), 1, 9)]


def large(rng, index):
    # 모든 마을이 이어져 있어 가장 가까운 곳 찾기를 n번 다 해야 한다
    if index == 0:  # 아무렇게나 이어진 마을
        return [66_000, connected(rng, 66_000, 66_000, 1, 9_000)]
    return [66_000, connected(rng, 66_000, 66_000, 1, 9_000, reach=3)]  # 길고 가는 모양: 거리가 크고 큐가 길게 이어진다
