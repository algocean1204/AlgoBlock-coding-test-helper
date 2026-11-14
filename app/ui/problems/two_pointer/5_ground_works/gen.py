LARGE = 2


def random_works(rng, rows, cols, count, amounts):
    works = []
    for _ in range(count):
        r1, r2 = sorted([rng.randint(0, rows - 1), rng.randint(0, rows - 1)])
        c1, c2 = sorted([rng.randint(0, cols - 1), rng.randint(0, cols - 1)])
        works.append([r1, c1, r2, c2, rng.choice(amounts)])
    return works


def small(rng):
    cases = [
        [1, 1, [[0, 0, 0, 0, 5]]],  # 가장 작은 입력, 0인 칸이 없다
        [1, 1, [[0, 0, 0, 0, 1000], [0, 0, 0, 0, -1000]]],  # 쌓고 파내 0으로 돌아온다
        [3, 3, [[1, 1, 1, 1, -1000]]],  # 가운데 한 칸만
        [3, 3, [[0, 0, 2, 2, 7], [0, 0, 2, 2, -7]]],  # 바닥 전체가 0으로 돌아온다
        [3, 3, [[2, 2, 2, 2, 1]]],  # 오른쪽 아래 모서리 한 칸
        [5, 5, [[0, 0, 4, 4, 2], [1, 1, 3, 3, -2]]],  # 가장자리만 남는다
        [1, 6, [[0, 1, 0, 3, 2], [0, 3, 0, 5, -2], [0, 0, 0, 0, 1]]],  # 한 행
        [6, 1, [[1, 0, 3, 0, 2], [3, 0, 5, 0, -2], [0, 0, 0, 0, 1]]],  # 한 열
        [4, 4, [[0, 0, 1, 1, 1], [2, 2, 3, 3, 1], [0, 2, 1, 3, -1], [2, 0, 3, 1, -1]]],  # 0인 칸이 없다
        [4, 5, [[0, 0, 2, 3, 3], [1, 1, 3, 4, -3], [0, 0, 0, 0, -3]]],
    ]
    for _ in range(6):
        rows, cols = rng.randint(2, 8), rng.randint(2, 8)
        cases.append([rows, cols, random_works(rng, rows, cols, rng.randint(1, 8), [-2, -1, 1, 2])])
    cases.append([30, 30, random_works(rng, 30, 30, 40, [-3, -2, -1, 1, 2, 3])])
    cases.append([1000, 1000, [[0, 0, 999, 999, 1000], [500, 0, 999, 999, -1000], [0, 500, 999, 999, -1000]]])  # 가장 큰 격자
    return cases


def random_small(rng):
    rows, cols = rng.randint(1, 5), rng.randint(1, 5)
    return [rows, cols, random_works(rng, rows, cols, rng.randint(1, 5), [-2, -1, 1, 2])]


def large(rng, index):
    if index == 0:  # 직사각형이 모두 커서 칸마다 더하는 풀이가 가장 오래 걸린다
        works = []
        for _ in range(30_000):
            r1, r2 = rng.randint(0, 200), rng.randint(799, 999)
            c1, c2 = rng.randint(0, 200), rng.randint(799, 999)
            amount = rng.randint(1, 1000) * rng.choice([-1, 1])
            works.append([r1, c1, r2, c2, amount])
        return [1000, 1000, works]
    return [1000, 1000, random_works(rng, 1000, 1000, 30_000, [-3, -2, -1, 1, 2, 3])]


def valid(rows, cols, works):
    return 1 <= rows <= 1000 and 1 <= cols <= 1000 and 1 <= len(works) <= 30_000 and all(
        len(work) == 5 and 0 <= work[0] <= work[2] < rows and 0 <= work[1] <= work[3] < cols and -1000 <= work[4] <= 1000 and work[4] != 0
        for work in works)
