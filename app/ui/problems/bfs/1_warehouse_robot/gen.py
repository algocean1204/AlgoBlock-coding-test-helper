LARGE = 2


def valid(floor):
    if not 1 <= len(floor) <= 100 or not 1 <= len(floor[0]) <= 100:
        return False
    if any(len(row) != len(floor[0]) or set(row) - set(".#SE") for row in floor):
        return False
    text = "".join(floor)
    return text.count("S") == 1 and text.count("E") == 1


def random_floor(rng, rows, cols, wall_num, wall_den):
    """선반을 wall_num/wall_den 비율로 흩고, 서로 다른 두 칸에 S와 E를 놓는다."""
    cells = [["#" if rng.chance(wall_num, wall_den) else "." for _ in range(cols)] for _ in range(rows)]
    start, end = rng.sample(range(rows * cols), 2)
    cells[start // cols][start % cols] = "S"
    cells[end // cols][end % cols] = "E"
    return ["".join(row) for row in cells]


def maze(rng, height, width):
    """길이 하나뿐인 미로((2*height+1) x (2*width+1)). S는 왼쪽 위 방, E는 오른쪽 아래 방."""
    cells = [["#"] * (2 * width + 1) for _ in range(2 * height + 1)]
    cells[1][1] = "."
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
        cells[r + nr + 1][c + nc + 1] = "."  # 두 방 사이의 벽을 튼다
        cells[2 * nr + 1][2 * nc + 1] = "."
        stack.append((nr, nc))
    cells[1][1] = "S"
    cells[2 * height - 1][2 * width - 1] = "E"
    return ["".join(row) for row in cells]


def small(rng):
    cases = [
        [["SE"]],
        [["ES"]],
        [["S", "E"]],
        [["E", ".", ".", "S"]],  # 세로로 긴 창고, 위로만 움직인다
        [["S.........", "#########.", "E........."]],  # 가로로 긴 창고, 끝까지 갔다가 되돌아온다
        [["S.#..", "..#..", "..#.E"]],  # 선반 벽에 막힌다
        [["S..", ".#.", "#E#"]],  # E가 선반에 둘러싸였다
        [["E..", "...", "..S"]],  # 위와 왼쪽으로만 간다
        [["S#.E", ".#.#", "...#"]],  # 아래로 갔다가 위로 돌아 올라간다
        [["S....", ".....", ".....", "....E"]],  # 빈터: 아무렇게나 가면 길어진다
        [[".....", ".###.", ".#E#.", ".#.#.", "S#..."]],  # 아래에서 둘러 들어간다
        [maze(rng, 9, 19)],
    ]
    for _ in range(5):
        cases.append([random_floor(rng, rng.randint(4, 9), rng.randint(4, 9), 3, 10)])
    cases.append([random_floor(rng, 6, 30, 1, 3)])
    return cases


def random_small(rng):
    rows, cols = rng.randint(1, 5), rng.randint(1, 5)
    if rows * cols < 2:
        cols = 2
    return [random_floor(rng, rows, cols, 1, 4)]


def large(rng, index):
    size = 100
    if index == 0:
        # 왼쪽 위 10 x 10 빈터를 지나 한 칸짜리 통로가 아래쪽 전체를 뱀처럼 오간다.
        # 모든 길을 따라가 보는 DFS는 빈터에서, 꺼낼 때 방문 표시를 하는 BFS는 통로에서 끝나지 않는다.
        cells = [["#"] * size for _ in range(size)]
        for r in range(10):
            for c in range(10):
                cells[r][c] = "."
        cells[10][9] = "."
        for k, r in enumerate(range(11, size, 2)):
            for c in range(size):
                cells[r][c] = "."
            if r + 1 < size:
                cells[r + 1][size - 1 if k % 2 == 0 else 0] = "."
        cells[0][0] = "S"
        cells[size - 1][size - 1] = "E"
        return [["".join(row) for row in cells]]
    cells = [["#" if rng.chance(1, 10) else "." for _ in range(size)] for _ in range(size)]  # 거의 빈 넓은 창고
    cells[0][0] = "S"
    cells[size - 1][size - 1] = "E"
    return [["".join(row) for row in cells]]
