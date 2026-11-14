LARGE = 2


def numbered(n, m):
    return [[r * m + c + 1 for c in range(m)] for r in range(n)]


def random_board(rng, n, m, high):
    return [[rng.randint(1, high) for _ in range(m)] for _ in range(n)]


def random_shape(rng, low, high):
    """n과 m 가운데 작은 값이 짝수인 크기."""
    while True:
        n, m = rng.randint(low, high), rng.randint(low, high)
        if min(n, m) % 2 == 0:
            return n, m


def small(rng):
    cases = [
        [[[5, 9], [7, 3]], 1],                    # 가장 작은 진열대
        [[[5, 9], [7, 3]], 4],                    # 칸 수만큼 돌면 제자리
        [[[5, 9], [7, 3]], 19999],
        [numbered(2, 5), 1],                      # 고리 하나, 가로로 긴 것
        [numbered(5, 2), 7],                      # 고리 하나, 세로로 긴 것
        [numbered(4, 4), 2],
        [numbered(4, 6), 10],                     # 바깥 고리 16칸, 안쪽 고리 6칸
        [numbered(6, 4), 5],
        [numbered(6, 6), 19],                     # 고리 세 개: 20칸, 12칸, 4칸
        [numbered(4, 7), 9],
        [numbered(7, 4), 18],                     # 바깥 고리는 제자리, 안쪽 고리만 움직인다
        [[[8] * 4 for _ in range(4)], 3],         # 모든 보석이 같은 번호
        [numbered(8, 8), 2999],
        [numbered(2, 100), 3000],
        [[[10000, 1], [1, 10000], [10000, 1]], 2],
    ]
    for _ in range(4):
        n, m = random_shape(rng, 2, 10)
        cases.append([random_board(rng, n, m, 10_000), rng.randint(1, 3000)])
    return cases


def valid(board, k):
    n, m = len(board), len(board[0]) if board else 0
    return (2 <= n <= 100 and 2 <= m <= 100 and min(n, m) % 2 == 0 and all(len(row) == m for row in board)
            and all(1 <= value <= 10_000 for row in board for value in row) and 1 <= k <= 100_000_000)


def random_small(rng):
    n, m = random_shape(rng, 2, 6)
    return [random_board(rng, n, m, 50), rng.randint(1, 60)]


def large(rng, index):
    if index == 0:
        return [random_board(rng, 100, 100, 10_000), 100_000_000]
    return [random_board(rng, 100, 58, 10_000), rng.randint(90_000_000, 99_999_999)]
