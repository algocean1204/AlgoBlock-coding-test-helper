LARGE = 0


def random_apples(rng, rows, count, low, high):
    return [[rng.randint(1, rows), rng.randint(low, high)] for _ in range(count)]


def small(rng):
    cases = [
        [1, [[1, 1]], 1],  # 가장 작은 입력
        [1, [[1, 400], [1, 1]], 2],  # 가장 큰 무게와 가장 작은 무게
        [2, [[2, 5], [2, 5], [2, 5]], 1],  # 1번 줄은 비었다
        [3, [[1, 7], [1, 7], [3, 9]], 2],  # 같은 무게만 있는 줄: 2번째가 없다
        [1, [[1, 10], [1, 20], [1, 30], [1, 40], [1, 50]], 5],  # 가장 가벼운 것이 k번째
        [1, [[1, 50], [1, 40], [1, 30], [1, 20], [1, 10]], 4],
        [5, [[5, 3], [5, 1], [5, 2], [1, 8]], 1],  # 사과가 처음과 끝 줄에만
        [4, [[1, 9], [1, 8], [2, 9], [2, 9], [2, 8], [3, 7], [4, 6], [4, 6], [4, 5], [4, 4]], 2],
        [2, [[1, 6], [1, 6], [1, 5], [1, 5], [1, 4], [2, 3], [2, 2], [2, 1]], 3],  # 같은 무게를 빼면 3번째가 달라진다
        [3, [[2, 100], [2, 90], [2, 80], [2, 70], [2, 60], [2, 50], [2, 40], [2, 30], [2, 20], [2, 10]], 10],  # 가장 큰 k
        [20, [[20, 400]], 1],  # 가장 많은 줄, 사과는 마지막 줄에 하나
    ]
    cases.append([20, random_apples(rng, 20, 160, 100, 400), 10])  # 가장 큰 입력
    cases.append([20, random_apples(rng, 20, 160, 1, 15), 3])
    for _ in range(5):
        rows = rng.randint(1, 8)
        cases.append([rows, random_apples(rng, rows, rng.randint(5, 40), 1, 10), rng.randint(1, 5)])
    return cases


def valid(rows, apples, k):
    return (1 <= rows <= 20 and 1 <= len(apples) <= 160 and 1 <= k <= 10
            and all(len(apple) == 2 and 1 <= apple[0] <= rows and 1 <= apple[1] <= 400 for apple in apples))


def random_small(rng):
    rows = rng.randint(1, 4)
    return [rows, random_apples(rng, rows, rng.randint(1, 10), 1, 5), rng.randint(1, 3)]


def large(rng, index):
    return []
