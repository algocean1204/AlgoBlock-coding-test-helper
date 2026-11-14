LARGE = 2


def valid(ground):
    if not (1 <= len(ground) <= 300 and 1 <= len(ground[0]) <= 300):
        return False
    return all(len(row) == len(ground[0]) and all(0 <= height <= 1_000_000 for height in row) for row in ground)


def grid(rng, rows, cols, low, high):
    return [[rng.randint(low, high) for _ in range(cols)] for _ in range(rows)]


def snake(rng, rows, cols, step):
    """짝수 행은 지나갈 수 있는 낮은 길, 홀수 행은 높은 벽이고 벽에는 양 끝을 번갈아 틈이 하나 있다.
    길은 오른쪽·왼쪽을 번갈아 가는 뱀 모양이고, 길 위의 높이는 한 걸음에 step 이하로만 바뀐다.
    걸음은 도착에 가까울수록 가팔라진다: 답 후보를 작은 것부터 올리는 풀이가 후보마다 길을 멀리까지 따라간다."""
    ground = [[1_000_000 - rng.randint(0, 50) for _ in range(cols)] for _ in range(rows)]
    path = []
    for r in range(0, rows, 2):
        columns = list(range(cols)) if (r // 2) % 2 == 0 else list(range(cols - 1, -1, -1))
        path += [(r, c) for c in columns]
        if r + 1 < rows:
            path.append((r + 1, columns[-1]))  # 벽의 틈
    level = rng.randint(0, 500_000)
    for i, (r, c) in enumerate(path):
        bound = 1 + step * i // len(path)
        level = min(500_000, max(0, level + rng.randint(-bound, bound)))
        ground[r][c] = level
    last_r, last_c = rows - 1, cols - 1
    if (last_r, last_c) not in path:  # 도착 칸이 벽이면 바로 위 길 칸과 이어 준다
        ground[last_r][last_c] = ground[last_r - 1][last_c] + rng.randint(0, step)
    return ground


def small(rng):
    cases = [
        [[[0, 1000000]]],
        [[[0], [7], [3]]],  # 한 열
        [[[0, 3, 1, 4, 1, 5]]],  # 한 행: 길이 하나뿐이다
        [[[4, 4, 4, 4], [4, 4, 4, 4], [4, 4, 4, 4]]],  # 모두 같은 높이
        [[[1000000, 0], [0, 1000000]]],
        [[[0, 9, 0, 0, 0, 0, 0], [0, 9, 0, 9, 9, 9, 0], [0, 9, 0, 9, 0, 0, 0], [0, 9, 0, 9, 0, 9, 9], [0, 0, 0, 9, 0, 0, 0]]],  # 위로 두 번 돌아가야 한다
        [[[0, 9, 0, 0, 0], [0, 9, 0, 9, 0], [0, 0, 0, 9, 0]]],  # 위로 한 번 돌아가면 턱이 없다
        [[[0, 2, 4], [0, 100, 2], [0, 3, 0]]],  # 턱 높이의 합은 왼쪽 아래 길(6)이 작고, 가장 높은 턱은 오른쪽 위 길(2)이 낮다
        [snake(rng, 9, 7, 3)],
        [snake(rng, 12, 10, 100000)],
    ]
    for rows, cols, high in ((3, 3, 9), (4, 6, 9), (6, 5, 30), (8, 8, 1000000), (10, 12, 99), (15, 12, 9)):
        cases.append([grid(rng, rows, cols, 0, high)])
    return cases


def random_small(rng):
    return [grid(rng, rng.randint(1, 4), rng.randint(1, 4), 0, 9)]


def large(rng, index):
    if index == 0:  # 높이가 제멋대로인 300 × 300: 답이 커서 후보를 하나씩 올리는 풀이는 수만 번 BFS를 돈다
        return [grid(rng, 300, 300, 0, 1_000_000)]
    return [snake(rng, 300, 300, 3000)]  # 4만 5천 칸을 지나는 뱀 모양 길: 오른쪽·아래로만은 갈 수 없다
