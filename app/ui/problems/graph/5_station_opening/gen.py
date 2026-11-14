LARGE = 2


def valid(n, tracks, queries):
    return (1 <= n <= 300 and len(tracks) <= 10_000
            and all(1 <= a <= n and 1 <= b <= n and a != b and 1 <= minutes <= 1_000 for a, b, minutes in tracks)
            and 1 <= len(queries) <= 50_000 and all(1 <= k <= n and 1 <= a <= k and 1 <= b <= k for k, a, b in queries))


def random_tracks(rng, low, high, count, longest):
    """low~high번 역 가운데 서로 다른 두 역을 잇는 선로 count개. 시간은 1~longest분."""
    return [rng.distinct(low, high, 2) + [rng.randint(1, longest)] for _ in range(count)]


def random_queries(rng, n, count, lowest_k=1):
    queries = []
    for _ in range(count):
        k = rng.randint(lowest_k, n)
        queries.append([k, rng.randint(1, k), rng.randint(1, k)])
    return queries


def small(rng):
    chain = [[k, k + 1, 1000] for k in range(1, 12)]
    complete = [[a, b, rng.randint(1, 50)] for a in range(1, 7) for b in range(a + 1, 7)]
    cases = [
        [1, [], [[1, 1, 1]]],
        [2, [], [[2, 1, 2], [1, 1, 1], [2, 2, 1]]],
        [2, [[1, 2, 1], [2, 1, 1000]], [[2, 1, 2], [2, 2, 1]]],  # 나중 선로가 더 길다
        [5, [[1, 2, 1], [2, 3, 1], [3, 4, 1], [4, 5, 1]], [[3, 1, 3], [5, 1, 5], [4, 4, 1], [2, 1, 2]]],  # 아직 닫힌 역까지의 거리도 고쳐 두어야 한다
        [4, [[1, 4, 1], [4, 2, 1], [1, 2, 5], [2, 3, 1]], [[2, 1, 2], [3, 1, 3], [4, 1, 3], [4, 3, 1]]],
        [4, [[1, 4, 3], [4, 2, 3], [2, 3, 1]], [[3, 1, 2], [4, 1, 2], [3, 2, 3], [4, 1, 3]]],  # 4번 역이 열려야 1번에서 나갈 수 있다
        [6, complete, [[1, 1, 1]] + [[k, a, b] for k in range(2, 7) for a, b in ((1, k), (k, 1), (2, k))]],
        [12, chain, [[12, 1, 12], [12, 12, 1], [11, 1, 11], [6, 6, 1]]],
        [110, [[k, k + 1, 1000] for k in range(1, 110)], [[110, 1, 110], [110, 110, 1], [109, 1, 109], [110, 1, 55], [60, 30, 1]]],  # 답이 10만 분을 넘는다: INF를 작게 잡으면 갈 수 없다고 본다
        [3, [[1, 3, 9], [1, 3, 2], [3, 1, 5], [3, 2, 4], [2, 3, 1], [1, 2, 20]], [[3, 1, 2], [2, 1, 2], [3, 2, 1]]],
        [6, [[1, 2, 2], [3, 4, 2], [5, 6, 2], [2, 6, 1]], [[6, 1, 6], [6, 3, 1], [4, 3, 4], [6, 1, 5], [5, 4, 1]]],  # 서로 닿지 않는 역이 있다
        [5, [[1, 5, 1], [5, 2, 1], [2, 4, 1], [4, 3, 1], [1, 3, 50]], [[5, 1, 3], [3, 1, 3], [4, 3, 1], [5, 3, 2], [2, 1, 2]]],  # k 순서가 뒤섞인 질문
    ]
    for _ in range(4):
        n = rng.randint(4, 10)
        cases.append([n, random_tracks(rng, 1, n, rng.randint(n - 2, 2 * n), rng.choice([5, 1000])), random_queries(rng, n, rng.randint(10, 25))])
    n = 15  # 큰 번호 역이 지름길이 된다
    hubs = [[rng.randint(1, 12), rng.randint(13, 15), rng.randint(1, 3)] for _ in range(12)]
    cases.append([n, random_tracks(rng, 1, 12, 14, 100) + hubs, random_queries(rng, n, 30, 6)])
    return cases


def random_small(rng):
    n = rng.randint(1, 6)
    tracks = random_tracks(rng, 1, n, rng.randint(0, 8), 5) if n > 1 else []
    return [n, tracks, random_queries(rng, n, rng.randint(1, 6))]


def large(rng, index):
    n = 300
    if index == 0:  # 번호가 가까운 역끼리만 선로 10,000개(띠 모양). k가 크고 (k, 출발역) 쌍이 거의 다르며 도착역은 먼 끝: 질문마다(쌍마다) 탐색하면 열린 역을 거의 다 본다
        tracks = []
        for _ in range(10_000):
            a = rng.randint(1, n - 1)
            tracks.append([a, min(n, a + rng.randint(1, 8)), rng.randint(1, 1_000)])
        queries = []
        while len(queries) < 50_000:
            k = rng.randint(201, n)
            a = rng.randint(1, k)
            b = rng.randint(k - 5, k) if a <= k // 2 else rng.randint(1, 6)
            queries.append([k, a, b])
        return [n, tracks, queries]
    # 선로 10,000개를 고르게. k가 1~300 모두 나온다: k마다 플로이드를 새로 돌리면 1³ + … + 300³ ≈ 20억 번
    tracks = [rng.distinct(1, n, 2) + [rng.randint(1, 1_000)] for _ in range(10_000)]
    return [n, tracks, random_queries(rng, n, 50_000)]
