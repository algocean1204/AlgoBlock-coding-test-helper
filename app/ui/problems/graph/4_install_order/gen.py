LARGE = 2


def dag_rules(rng, n, count):
    """무작위 순서 perm에서 앞에 있는 패키지가 뒤에 있는 패키지보다 먼저인 규칙 count개(사이클이 없다)."""
    perm = rng.shuffle(list(range(1, n + 1)))
    rules = []
    for _ in range(count):
        i, j = sorted(rng.distinct(0, n - 1, 2))
        rules.append([perm[i], perm[j]])
    return perm, rules


def valid(n, rules):
    return 1 <= n <= 100_000 and len(rules) <= 100_000 and all(1 <= a <= n and 1 <= b <= n and a != b for a, b in rules)


def any_rules(rng, n, count):
    return [rng.distinct(1, n, 2) for _ in range(count)]


def small(rng):
    cases = [
        [1, []],
        [2, [[2, 1]]],
        [2, [[1, 2], [2, 1]]],
        [3, [[2, 1]]],  # 2번을 설치하는 순간 풀린 1번이 3번보다 먼저
        [3, [[1, 2], [1, 2], [2, 3]]],  # 같은 규칙이 두 번
        [5, [[1, 2], [2, 3], [3, 2], [4, 5]]],  # 사이클 밖의 패키지는 설치할 수 있지만 모두 설치할 수는 없다
        [6, [[6, 5], [5, 4], [4, 3], [3, 2], [2, 1]]],
        [10, []],
        [6, [[5, 1], [6, 2], [1, 3]]],
        [7, [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 3]]],  # 사이클이 뒤쪽에
        [8, [[8, 1], [8, 2], [7, 1], [3, 1], [3, 2], [7, 2], [8, 2]]],
    ]
    for _ in range(4):
        n = rng.randint(5, 30)
        cases.append([n, dag_rules(rng, n, rng.randint(n // 2, 2 * n))[1]])
    for _ in range(2):
        n = rng.randint(5, 12)
        cases.append([n, any_rules(rng, n, rng.randint(2, n))])
    return cases


def random_small(rng):
    n = rng.randint(1, 7)
    if n == 1:
        return [1, []]
    if rng.chance(3, 4):
        return [n, dag_rules(rng, n, rng.randint(0, 8))[1]]
    return [n, any_rules(rng, n, rng.randint(1, 6))]


def large(rng, index):
    n = 100_000
    perm, rules = dag_rules(rng, n, n - 2)
    if index == 0:  # 모두 설치할 수 있다. 처음부터 설치할 수 있는 패키지가 수만 개라 목록에서 min을 찾는 풀이가 느리다
        rules += [[perm[0], perm[-1]], [perm[1], perm[-2]]]
    else:  # 맨 뒤 두 패키지가 서로를 기다린다: 거의 다 설치한 뒤에야 불가능을 안다
        rules += [[perm[-2], perm[-1]], [perm[-1], perm[-2]]]
    return [n, rules]
