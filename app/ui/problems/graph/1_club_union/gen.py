LARGE = 3


def valid(n, merges):
    return 1 <= n <= 100_000 and len(merges) <= 100_000 and all(1 <= a <= n and 1 <= b <= n and a != b for a, b in merges)


def random_merges(rng, low, high, count):
    """low~high번 동아리 가운데 서로 다른 두 동아리를 고른 기록 count개."""
    return [rng.distinct(low, high, 2) for _ in range(count)]


def small(rng):
    cases = [
        [1, []],
        [2, [[1, 2]]],
        [2, [[2, 1], [1, 2], [2, 1]]],
        [3, [[1, 2], [3, 2], [1, 3]]],  # 대표가 아닌 번호를 바로 이으면 1번이 떨어져 나간다
        [3, [[1, 2], [3, 1]]],  # parent에 대표가 아닌 값이 남는다
        [3, [[2, 1], [2, 3], [3, 1]]],  # 대표가 아닌 a번을 b번 아래에 바로 이어도 틀린다
        [7, []],
        [8, [[1, 2], [1, 2], [1, 2]]],  # 같은 기록이 여러 번
        [7, [[7, 6], [6, 5], [5, 4], [4, 3], [3, 2], [2, 1]]],
        [6, [[1, 2], [3, 4], [5, 6], [1, 3], [3, 5]]],
        [100000, [[1, 2], [99999, 100000]]],  # 기록에 나오지 않은 동아리가 대부분
        [10, [[1, 10], [2, 10], [3, 10], [4, 10], [5, 6], [6, 7], [7, 5]]],
    ]
    for _ in range(3):
        n = rng.randint(5, 40)
        cases.append([n, random_merges(rng, 1, n, rng.randint(1, n))])
    for _ in range(3):  # 이미 같은 연합인 기록이 많다
        n = rng.randint(5, 20)
        cases.append([n, random_merges(rng, 1, n, rng.randint(n, 3 * n))])
    return cases


def random_small(rng):
    n = rng.randint(1, 8)
    if n == 1:
        return [1, []]
    return [n, random_merges(rng, 1, n, rng.randint(0, 9))]


def large(rng, index):
    n = 100_000
    if index == 2:  # 긴 줄 두 개: 앞 절반은 [k, k+1], 뒤 절반은 [k+1, k]. 재귀로 대표를 찾으면 합치는 방향과 상관없이 한쪽 줄이 5만 칸이 된다
        return [n, [[k, k + 1] for k in range(1, 50_000)] + [[k + 1, k] for k in range(50_001, 100_000)]]
    if index == 0:  # [n, 새 동아리]: a쪽 대표를 b쪽 아래에 두는 풀이는 n번의 줄이 매번 한 칸씩 길어진다
        merges = [[n, k] for k in range(n - 1, 0, -1)]
        merges.append([n, 1])
        return [n, merges]
    # [새 동아리, 1]: b쪽 대표를 a쪽 아래에 두는 풀이는 1번의 줄이 매번 한 칸씩 길어진다. 나머지는 무작위로 합친다
    merges = [[k, 1] for k in range(2, 80_001)]
    merges += random_merges(rng, 80_001, n, n - len(merges))
    return [n, merges]
