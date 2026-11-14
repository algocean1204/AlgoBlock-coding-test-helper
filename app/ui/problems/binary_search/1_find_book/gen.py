LARGE = 2


def small(rng):
    cases = [
        [[7], [7]],  # 책이 한 권, 그 책을 찾는다
        [[7], [6, 8]],  # 책이 한 권, 앞뒤 번호는 없다
        [[1, 2], [2, 1, 3]],
        [[5, 10], [10, 5, 7, 4, 11]],
        [[2, 4, 6, 8, 10], [2, 10, 6, 5, 11, 1]],  # 처음·끝·가운데·사이·뒤·앞
        [[1, 1000000000], [1000000000, 1, 999999999]],  # 가장 큰 값
        [[3, 6, 9, 12, 15, 18, 21], [21, 21, 3, 3, 12, 13]],  # 같은 번호를 여러 번 찾는다
        [list(range(10, 400, 10)), [10, 390, 200, 205, 5, 395]],
    ]
    for _ in range(8):
        books = sorted(rng.distinct(1, 200, rng.randint(1, 60)))
        queries = [rng.randint(1, 205) for _ in range(rng.randint(1, 30))]
        cases.append([books, queries])
    return cases


def valid(books, queries):
    return (1 <= len(books) <= 100_000 and 1 <= len(queries) <= 100_000 and all(1 <= x <= 1_000_000_000 for x in books + queries)
            and all(books[i] < books[i + 1] for i in range(len(books) - 1)))


def random_small(rng):
    books = sorted(rng.distinct(1, 30, rng.randint(1, 10)))
    return [books, [rng.randint(1, 31) for _ in range(rng.randint(1, 8))]]


def large(rng, index):
    books = [2 * value for value in sorted(rng.distinct(1, 500_000_000, 100_000))]  # 짝수 번호만
    if index == 0:  # 찾는 번호가 모두 홀수라 하나도 없다: 앞에서부터 훑으면 매번 끝까지 본다
        queries = [2 * rng.randint(1, 500_000_000) - 1 for _ in range(100_000)]
    else:  # 반은 있는 번호, 반은 없는 번호
        queries = [rng.choice(books) if rng.chance(1, 2) else 2 * rng.randint(1, 500_000_000) - 1 for _ in range(100_000)]
    return [books, queries]
