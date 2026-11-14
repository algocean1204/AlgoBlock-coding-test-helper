LARGE = 0


def matrix(n, pairs):
    """선로 쌍 목록으로 n × n 표를 만든다(양쪽 방향)."""
    rails = [[0] * n for _ in range(n)]
    for a, b in pairs:
        rails[a][b] = rails[b][a] = 1
    return rails


def everything(n):
    return [(a, b) for a in range(n) for b in range(a + 1, n)]


def random_rails(rng, n, numerator, denominator):
    return matrix(n, [pair for pair in everything(n) if rng.chance(numerator, denominator)])


def small(rng):
    cases = [
        [matrix(2, [(0, 1)])],
        [matrix(2, [])],
        [matrix(10, [(i, i + 1) for i in range(9)])],  # 한 줄: 길은 하나
        [matrix(10, [(i, (i + 1) % 10) for i in range(10)])],  # 둥근 고리: 바로 가거나 한 바퀴 돌아가거나
        [matrix(10, everything(10))],  # 모두 이어졌다: 가장 많은 109,601가지
        [matrix(10, [pair for pair in everything(10) if pair != (0, 9)])],
        [matrix(9, [(4, i) for i in range(9) if i != 4])],  # 가운데 4번을 거쳐야만 간다
        [matrix(8, everything(4) + [(a + 4, b + 4) for a, b in everything(4)] + [(3, 4)])],  # 두 무리를 다리 하나가 잇는다
        [matrix(7, [(1, 2), (2, 3), (3, 6), (1, 6)])],  # 0번 역에 선로가 없다
        [matrix(6, [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 5)])],
        [matrix(5, [(0, 4)] + [(a, b) for a, b in everything(4) if a > 0])],  # 바로 가는 길 하나와, 0번에서 나갈 다른 선로가 없다
        [matrix(6, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2), (4, 5)])],  # 고리 둘을 지나 간다
    ]
    for n, numerator, denominator in ((5, 1, 2), (6, 2, 3), (7, 1, 3), (8, 1, 2), (9, 2, 5), (10, 1, 3), (10, 3, 5)):
        cases.append([random_rails(rng, n, numerator, denominator)])
    return cases


def random_small(rng):
    n = rng.randint(2, 7)
    return [random_rails(rng, n, rng.randint(1, 4), 5)]


def valid(rails):
    n = len(rails)
    return (2 <= n <= 10 and all(len(row) == n for row in rails)
            and all(rails[a][b] in (0, 1) and rails[a][b] == rails[b][a] for a in range(n) for b in range(n))
            and all(rails[a][a] == 0 for a in range(n)))


def large(rng, index):
    return []
