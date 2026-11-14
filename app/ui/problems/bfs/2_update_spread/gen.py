LARGE = 2
N, CABLES = 30_000, 90_000


def valid(n, cables, start, offline):
    if not (2 <= n <= N and 1 <= len(cables) <= CABLES and 1 <= start <= n and 0 <= len(offline) <= n - 1):
        return False
    pairs = {(min(a, b), max(a, b)) for a, b in cables}
    if len(pairs) != len(cables) or not all(1 <= a <= n and 1 <= b <= n and a != b for a, b in cables):
        return False
    return len(set(offline)) == len(offline) and all(1 <= v <= n and v != start for v in offline)


def random_cables(rng, n, extra):
    """무작위 케이블을 extra번 더해 본다(겹치거나 자기 자신이면 버린다). 적어도 하나는 남는다."""
    seen = set()
    cables = []

    def add(a, b):
        key = (min(a, b), max(a, b))
        if a != b and key not in seen:
            seen.add(key)
            cables.append([a, b] if rng.chance(1, 2) else [b, a])

    add(1, 2)
    for _ in range(extra):
        add(rng.randint(1, n), rng.randint(1, n))
    return rng.shuffle(cables)


def pick(rng, n, cables, off_count):
    """출발 서버 하나(케이블이 둘 이상 붙은 서버가 있으면 그 가운데서)와, 그 서버가 아닌 꺼진 서버 off_count대."""
    degree = [0] * (n + 1)
    for a, b in cables:
        degree[a] += 1
        degree[b] += 1
    busy = [v for v in range(1, n + 1) if degree[v] >= 2]
    start = rng.choice(busy) if busy else rng.randint(1, n)
    others = [v for v in range(1, n + 1) if v != start]
    return [n, cables, start, rng.sample(others, min(off_count, len(others)))]


def small(rng):
    cases = [
        [2, [[1, 2]], 1, []],
        [2, [[1, 2]], 2, [1]],  # 이웃이 꺼져 있다: [0, 1]
        [6, [[1, 2], [1, 3], [1, 4], [1, 5], [1, 6]], 1, []],  # 모두 1분에 받는다
        [6, [[1, 2], [1, 3], [1, 4], [1, 5], [1, 6]], 3, []],  # 가운데를 거쳐 2분에 넷
        [5, [[1, 2], [2, 3], [3, 4], [4, 5]], 3, []],  # 한 줄 가운데에서 출발
        [5, [[1, 2], [2, 3], [3, 4], [4, 5]], 1, [3]],  # 한 줄이 꺼진 서버에서 끊긴다
        [5, [[2, 1], [3, 2], [4, 2], [5, 2]], 5, [1]],  # 꺼진 서버가 가장 먼 자리에 있다
        [3, [[1, 2], [2, 3], [3, 1]], 2, []],  # 세모
        [8, [[1, 2], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8]], 1, []],  # 출발 서버와 이어지지 않은 긴 줄
        [7, [[1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [6, 7], [4, 7]], 1, [2]],  # 고리 한쪽이 꺼져 반대쪽으로 돌아간다
        [5, [[a, b] for a in range(1, 6) for b in range(a + 1, 6)], 4, [1, 2]],  # 모두가 서로 이어졌다
        [9, [[1, 2], [2, 3], [3, 1], [3, 4], [4, 5], [5, 3], [5, 6], [6, 7], [7, 5], [8, 9]], 9, []],  # 출발 서버 둘만 이어졌다
        [7, [[2, 4], [4, 6], [6, 1], [2, 3], [3, 5], [5, 7], [7, 1], [4, 5]], 2, [6]],
    ]
    parents = [[v, rng.randint(1, v - 1)] for v in range(2, 41)]  # 나무 모양
    cases.append(pick(rng, 40, rng.shuffle(parents), 3))
    for n, extra, off in ((12, 14, 1), (25, 30, 0), (40, 45, 4), (60, 70, 6), (60, 160, 10)):
        cases.append(pick(rng, n, random_cables(rng, n, extra), off))
    return cases


def random_small(rng):
    n = rng.randint(3, 8)
    return pick(rng, n, random_cables(rng, n, rng.randint(n - 1, n + 6)), rng.randint(0, 2))


def large(rng, index):
    if index == 0:
        # 1-2-3-…-m 한 줄을 먼저 적고, 1번에서 먼 쪽 서버부터 거꾸로 지름길을 잇는다.
        # DFS로 고쳐 가는 풀이는 한 줄 끝까지 내려간 뒤 지름길마다 줄 절반을 다시 고친다.
        # 줄에 붙은 나머지 서버는 모두 꺼져 있다.
        m = N - 200
        cables = [[v, v + 1] for v in range(1, m)]
        cables += [[1, v] for v in range(m, 3, -2)]
        cables += [[v, rng.randint(2, m)] for v in range(m + 1, N + 1)]
        return [N, cables, 1, list(range(m + 1, N + 1))]
    labels = rng.shuffle(list(range(1, N + 1)))
    joined = labels[:-100]  # 마지막 100대는 어느 케이블에도 이어지지 않는다
    seen = set()
    cables = []
    for i in range(1, len(joined)):
        a, b = joined[i], joined[rng.randint(0, i - 1)]
        seen.add((min(a, b), max(a, b)))
        cables.append([a, b])
    while len(cables) < CABLES:
        a, b = rng.choice(joined), rng.choice(joined)
        if a != b and (min(a, b), max(a, b)) not in seen:
            seen.add((min(a, b), max(a, b)))
            cables.append([a, b])
    start = joined[0]
    return [N, rng.shuffle(cables), start, rng.sample(joined[1:], 3_000)]
