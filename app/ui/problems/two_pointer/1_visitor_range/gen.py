LARGE = 2


def random_queries(rng, days, count):
    queries = []
    for _ in range(count):
        start, end = rng.randint(1, days), rng.randint(1, days)
        queries.append([min(start, end), max(start, end)])
    return queries


def small(rng):
    cases = [
        [[0], [[1, 1]]],
        [[10000], [[1, 1], [1, 1], [1, 1]]],
        [[4, 6], [[1, 2], [2, 2], [1, 1]]],
        [[5, 5, 5, 5], [[1, 4], [2, 3], [4, 4]]],
        [[0, 0, 0], [[1, 3], [2, 2]]],
        [[9, 0, 0, 4, 0, 8], [[2, 3], [1, 6], [3, 5], [6, 6], [1, 1]]],
        [[0, 7, 0, 0, 3], [[1, 2], [3, 4], [2, 5], [5, 5]]],
        [[1, 2, 3, 4, 5, 6, 7, 8], [[8, 8], [7, 8], [1, 8], [2, 7], [4, 5]]],
        [[10000] * 100, [[1, 100], [50, 100], [1, 1], [100, 100]]],
    ]
    for _ in range(6):
        days = rng.randint(5, 40)
        visitors = [rng.randint(0, 20) for _ in range(days)]
        cases.append([visitors, random_queries(rng, days, rng.randint(3, 15))])
    visitors = [rng.randint(0, 10000) for _ in range(150)]
    cases.append([visitors, [[1, 150]] + random_queries(rng, 150, 20)])
    return cases


def random_small(rng):
    days = rng.randint(1, 8)
    visitors = [rng.randint(0, 5) for _ in range(days)]
    return [visitors, random_queries(rng, days, rng.randint(1, 6))]


def large(rng, index):
    days = 100_000
    visitors = [rng.randint(0, 10000) for _ in range(days)]
    if index == 0:  # 질문마다 거의 전체 구간: 다시 더하는 풀이가 가장 오래 걸린다
        queries = [[rng.randint(1, 1000), rng.randint(days - 999, days)] for _ in range(50_000)]
    else:
        queries = random_queries(rng, days, 50_000)
    return [visitors, queries]


def valid(visitors, queries):
    days = len(visitors)
    return 1 <= days <= 100_000 and all(0 <= count <= 10000 for count in visitors) and 1 <= len(queries) <= 50_000 and all(
        len(query) == 2 and 1 <= query[0] <= query[1] <= days for query in queries)
