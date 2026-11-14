LARGE = 2


def make_tree(rng, n, reach):
    """0번이 꼭대기인 쉼터 n개. 번호는 섞여 있고, 새 쉼터는 바로 앞 reach개 가운데 하나 아래에 붙는다(1이면 한 줄).
    길은 [위, 아래]와 [아래, 위]가 섞이고 순서도 섞인다. (길 목록, 부모 목록)."""
    order = [0] + rng.shuffle(list(range(1, n)))
    up = [-1] * n
    for k in range(1, n):
        up[order[k]] = order[rng.randint(max(0, k - reach), k - 1)]
    trails = [[up[v], v] if rng.chance(1, 2) else [v, up[v]] for v in order[1:]]
    return rng.shuffle(trails), up


def course_sum(rng, energy, up):
    """실제로 있는 내리막 코스 하나의 합(답이 0이 되지 않게 target으로 쓴다)."""
    v = rng.randint(0, len(energy) - 1)
    total = energy[v]
    while up[v] != -1 and rng.chance(9, 10):
        v = up[v]
        total += energy[v]
    return total


def random_case(rng, n, reach, low, high):
    trails, up = make_tree(rng, n, reach)
    energy = [rng.randint(low, high) for _ in range(n)]
    target = course_sum(rng, energy, up) if rng.chance(4, 5) else rng.randint(low, high)
    return [trails, energy, target]


def small(rng):
    star = rng.shuffle([5, 5, 5, 10, 10, 10])
    cases = [
        [[], [5], 5],
        [[], [5], 0],
        [[[1, 0]], [3, -3], 0],  # 아래쪽 쉼터가 앞에 적혀 있다
        [[[i, i + 1] for i in range(7)], [0] * 8, 0],  # 모든 코스의 합이 0이다
        [[[0, i + 1] for i in range(6)], [0] + star, 5],  # 갈래끼리 이으면 합이 5인 가짜 코스가 생긴다
        [[[i + 1, i] for i in range(39)], [1000] * 40, 40000],  # 0번에서 맨 끝까지 내려가야 하나 나온다
        [[[i + 1, i] for i in range(39)], [-1000] * 40, -50000000],
        [[[0, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 6]], [1, 2, -2, -2, 2, 1, 1], 1],
    ]
    for n, reach, low, high in ((10, 1, -2, 2), (15, 15, -1, 1), (25, 2, -3, 3), (40, 3, -5, 5), (60, 60, -2, 2), (80, 2, -1000, 1000), (100, 4, -1, 1)):
        cases.append(random_case(rng, n, reach, low, high))
    return cases


def random_small(rng):
    n = rng.randint(1, 9)
    return random_case(rng, n, rng.randint(1, n), -2, 2)


def large(rng, index):
    n = 50_000
    if index == 0:  # 5만 개가 한 줄: 쉼터마다 올라가며 더하면 약 12억 번, 재귀는 5만 번 깊어진다
        trails, up = make_tree(rng, n, 1)
        return [trails, [rng.randint(-1, 1) for _ in range(n)], 0]
    # 2만 5천 개가 한 줄로 이어진 등줄기에 나머지가 한 칸씩 매달려 있다
    order = [0] + rng.shuffle(list(range(1, n)))
    up = [-1] * n
    for k in range(1, n):
        up[order[k]] = order[k - 1] if k < 25_000 else order[rng.randint(0, 24_999)]
    trails = rng.shuffle([[up[v], v] if rng.chance(1, 2) else [v, up[v]] for v in order[1:]])
    energy = [rng.randint(-1000, 1000) for _ in range(n)]
    return [trails, energy, course_sum(rng, energy, up)]


def valid(trails, energy, target):
    n = len(energy)
    if not (1 <= n <= 50_000 and len(trails) == n - 1 and all(-1000 <= e <= 1000 for e in energy) and -50_000_000 <= target <= 50_000_000):
        return False
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        if not (0 <= a < n and 0 <= b < n and a != b):
            return False
        neighbors[a].append(b)
        neighbors[b].append(a)
    seen, stack = {0}, [0]  # 길 n - 1개로 모든 쉼터가 이어지면 두 쉼터 사이의 길은 하나뿐이다(트리)
    while stack:
        for nxt in neighbors[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == n
