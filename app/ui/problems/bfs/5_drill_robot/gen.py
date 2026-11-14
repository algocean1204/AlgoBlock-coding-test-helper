LARGE = 2


def valid(mine, drill):
    if not 1 <= len(mine) <= 120 or not 1 <= len(mine[0]) <= 120 or not 0 <= drill <= 12:
        return False
    if any(len(row) != len(mine[0]) or set(row) - {0, 1} for row in mine):
        return False
    return mine[0][0] == 0 and mine[-1][-1] == 0


def random_mine(rng, rows, cols, rock_num, rock_den):
    mine = [[1 if rng.chance(rock_num, rock_den) else 0 for _ in range(cols)] for _ in range(rows)]
    mine[0][0] = 0
    mine[rows - 1][cols - 1] = 0
    return mine


def sparse_mine(rng, rows, cols, rocks):
    """바위가 정확히 rocks개(출발·도착 칸 빼고)."""
    mine = [[0] * cols for _ in range(rows)]
    for spot in rng.sample(range(1, rows * cols - 1), rocks):
        mine[spot // cols][spot % cols] = 1
    return mine


def maze(rng, height, width):
    """방 height x width개를 길 하나로만 이은 미로. 방은 (짝수, 짝수) 칸이고 나머지는 바위다."""
    rows, cols = 2 * height - 1, 2 * width - 1
    mine = [[1] * cols for _ in range(rows)]
    mine[0][0] = 0
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        r, c = stack[-1]
        options = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                   if 0 <= r + dr < height and 0 <= c + dc < width and (r + dr, c + dc) not in seen]
        if not options:
            stack.pop()
            continue
        nr, nc = rng.choice(options)
        seen.add((nr, nc))
        mine[r + nr][c + nc] = 0  # 두 방 사이를 튼다
        mine[2 * nr][2 * nc] = 0
        stack.append((nr, nc))
    return mine


def small(rng):
    cases = [
        [[[0]], 0],  # 출발 칸이 곧 도착 칸
        [[[0, 0]], 0],
        [[[0, 1, 0]], 0],  # 드릴이 없다
        [[[0, 1, 0]], 1],
        [[[0], [1], [1], [0]], 2],  # 드릴을 남김없이 써야 한다
        [[[0, 1, 1, 0]], 2],
        [[[0, 1, 1], [1, 1, 1], [1, 1, 0]], 3],
        [[[0, 1, 1], [1, 1, 1], [1, 1, 0]], 2],
        [[[0, 0, 0, 1], [1, 0, 0, 1], [0, 0, 1, 0]], 1],  # 드릴을 먼저 쓰고 온 길이 같은 칸을 먼저 차지한다
        [[[0, 0, 1, 1], [0, 1, 1, 0]], 1],  # 한 길에서 뚫은 바위를 다른 길이 공짜로 지나면 안 된다
        [[[0, 0, 1, 0], [1, 0, 0, 1], [0, 0, 1, 0]], 1],  # 드릴을 쓴 길과 아낀 길이 같은 거리로 같은 칸에 닿는다
        [[[0, 1, 0]], 2],  # 드릴이 남은 채 도착한다
        [[[0, 1, 1, 0]], 3],
    ]
    labyrinth = maze(rng, 8, 10)
    cases.append([labyrinth, 0])  # 드릴 없이 미로를 끝까지 돈다
    cases.append([labyrinth, 2])  # 바위 벽 두 곳을 뚫어 지름길을 낸다
    cases.append([random_mine(rng, 8, 8, 2, 5), 3])
    cases.append([random_mine(rng, 12, 12, 1, 3), 2])
    cases.append([random_mine(rng, 10, 20, 2, 5), 1])
    cases.append([[[0, 0, 0], [1, 0, 1], [0, 0, 1], [0, 1, 1], [0, 1, 0]], 1])  # 예시 3을 뒤집은 모양: 드릴을 쓴 길이 더 먼저 닿는다
    cases.append([sparse_mine(rng, 10, 10, 14), 12])
    return cases


def random_small(rng):
    rows, cols = rng.randint(1, 4), rng.randint(1, 4)
    return [random_mine(rng, rows, cols, 2, 5), rng.choice([0, 1, 1, 2, 2, 3])]


def large(rng, index):
    if index == 0:
        return [random_mine(rng, 120, 120, 7, 20), 12]  # 바위가 35%: 뚫을 바위 12개를 고르는 조합은 셀 수 없이 많다
    # 빈 줄과 바위 줄이 번갈아 있고 바위 줄의 틈은 양 끝을 번갈아 난다: 드릴 12번으로 어느 바위 줄을 뚫을지 정해야 한다
    rows, cols = 119, 120
    mine = [[0] * cols for _ in range(rows)]
    for k, r in enumerate(range(1, rows, 2)):
        for c in range(cols):
            mine[r][c] = 1
        mine[r][cols - 1 if k % 2 == 0 else 0] = 0
    return [mine, 12]
