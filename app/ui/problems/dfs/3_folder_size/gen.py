LARGE = 2


def make_tree(rng, n, reach):
    """0번이 맨 바깥인 폴더 n개. 번호는 섞여 있고, 새 폴더는 바로 앞 reach개 가운데 하나에 들어간다(1이면 한 줄)."""
    order = [0] + rng.shuffle(list(range(1, n)))
    parent = [-1] * n
    for k in range(1, n):
        parent[order[k]] = order[rng.randint(max(0, k - reach), k - 1)]
    return parent, order


def totals(parent, files, order):
    """order는 바깥 폴더가 안쪽 폴더보다 먼저 나오는 순서다(만들 때의 순서)."""
    total = list(files)
    for folder in reversed(order[1:]):
        total[parent[folder]] += total[folder]
    return total


def pick_limit(rng, total):
    """어느 폴더의 전체 용량과 똑같은 값을 고른다('이상'의 경계가 실제로 나오게)."""
    return max(1, rng.choice(total))


def random_case(rng, n, reach, high):
    parent, order = make_tree(rng, n, reach)
    files = [rng.randint(0, high) for _ in range(n)]
    return [parent, files, pick_limit(rng, totals(parent, files, order))]


def small(rng):
    cases = [
        [[-1], [0], 1],
        [[-1], [10000], 10000],
        [[-1, 0], [0, 5], 5],
        [[-1, 2, 3, 4, 5, 0], [1, 1, 1, 1, 1, 1], 3],  # 안쪽 폴더일수록 번호가 작다
        [[-1, 0, 1, 2, 3], [0, 0, 0, 0, 7], 7],  # 파일이 가장 안쪽에만 있다
        [[-1, 0, 0, 0, 0, 0, 0, 0, 0, 0], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 6],
        [[-1, 0, 1, 0, 3], [0, 0, 0, 0, 0], 1],
        [[-1, 4, 1, 1, 0, 2, 2], [10000] * 7, 1_000_000_000],
    ]
    for n, reach, high in ((10, 1, 9), (12, 2, 5), (30, 3, 20), (50, 50, 10), (80, 4, 10000), (120, 2, 100), (120, 120, 3), (100, 1, 10000)):
        cases.append(random_case(rng, n, reach, high))
    return cases


def random_small(rng):
    n = rng.randint(1, 8)
    case = random_case(rng, n, rng.randint(1, n), 5)
    if rng.chance(1, 3):
        case[2] = rng.randint(1, 20)
    return case


def large(rng, index):
    n = 100_000
    if index == 0:  # 10만 겹으로 들어 있다: 폴더마다 다시 훑으면 약 50억 번, 재귀는 10만 번 깊어진다
        return random_case(rng, n, 1, 10000)
    # 5만 겹 한 줄 아래에 폴더 5만 개가 매달려 있다
    order = [0] + rng.shuffle(list(range(1, n)))
    parent = [-1] * n
    for k in range(1, n):
        parent[order[k]] = order[k - 1] if k < 50_000 else order[49_999]
    files = [rng.randint(0, 10000) for _ in range(n)]
    return [parent, files, pick_limit(rng, totals(parent, files, order))]


def valid(parent, files, limit):
    n = len(parent)
    if not (1 <= n <= 100_000 and parent[0] == -1 and len(files) == n and 1 <= limit <= 1_000_000_000):
        return False
    if not all(0 <= p < n for p in parent[1:]) or not all(0 <= size <= 10_000 for size in files):
        return False
    children = [[] for _ in range(n)]
    for folder in range(1, n):
        children[parent[folder]].append(folder)
    reached, stack = 0, [0]  # 0번에서 안쪽으로 모든 폴더에 닿으면 고리 없이 하나의 트리다
    while stack:
        folder = stack.pop()
        reached += 1
        stack.extend(children[folder])
    return reached == n
