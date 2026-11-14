LARGE = 2


def valid(building):
    if not 1 <= len(building) <= 300 or not 1 <= len(building[0]) <= 300:
        return False
    if any(len(row) != len(building[0]) or set(row) - set(".#FSE") for row in building):
        return False
    text = "".join(building)
    return text.count("S") == 1 and "F" in text and "E" in text


def random_building(rng, rows, cols, wall_num, wall_den, fires, exits):
    """벽을 흩고, 서로 다른 칸에 S 하나, F fires개, E exits개를 놓는다."""
    cells = [["#" if rng.chance(wall_num, wall_den) else "." for _ in range(cols)] for _ in range(rows)]
    spots = rng.sample(range(rows * cols), 1 + fires + exits)
    for i, spot in enumerate(spots):
        cells[spot // cols][spot % cols] = "S" if i == 0 else ("F" if i <= fires else "E")
    return ["".join(row) for row in cells]


def snake(rows, cols):
    """한 칸짜리 통로가 줄마다 왼쪽·오른쪽 끝을 번갈아 돌며 내려간다. (0, 0)에서 시작해 마지막 통로 줄 끝에서 끝난다."""
    cells = [["#"] * cols for _ in range(rows)]
    last = None
    for k, r in enumerate(range(0, rows, 2)):
        for c in range(cols):
            cells[r][c] = "."
        last = (r, 0 if k % 2 == 1 else cols - 1)
        if r + 2 < rows:
            cells[r + 1][cols - 1 if k % 2 == 0 else 0] = "."
    return cells, last


def small(rng):
    cases = [
        [["SEF"]],  # 사람과 불이 1분에 함께 닿는다
        [["SE.F"]],
        [["S", "E", "F"]],
        [["FS", "#E"]],
        [["FSE"]],  # 불이 바로 옆이지만 한 발 앞선다
        [["F#S.E", "##..F"]],  # 처음 찾은 F는 갇혀 있고 두 번째 F가 비상구를 막는다
        [["F#E", "##.", "S.."]],  # 불이 닿지 않는 칸만 지나간다
        [["E.#", "##S", "F.#"]],  # 사람이 갇혀 있다
        [["E.......E", "#.#####.#", "F...S...F"]],  # 양쪽 불이 두 비상구를 모두 막는다
        [["F#.....", "##.###.", "S.....E", "#.#####", "#..F..."]],
        [["E...F", ".....", "..S..", ".....", "F...E"]],
    ]
    cells, last = snake(9, 13)  # 불이 바로 뒤에서 쫓아오는 긴 통로
    cells[0][0], cells[0][1] = "F", "S"
    cells[last[0]][last[1]] = "E"
    cases.append([["".join(row) for row in cells]])
    for rows, cols, fires, exits in ((5, 7, 1, 1), (8, 8, 2, 2), (10, 12, 3, 2), (12, 15, 2, 3), (15, 15, 4, 3), (6, 25, 2, 2)):
        cases.append([random_building(rng, rows, cols, 1, 4, fires, exits)])
    return cases


def random_small(rng):
    rows, cols = rng.randint(1, 5), rng.randint(1, 5)
    if rows * cols < 3:
        rows, cols = 1, 3 + rng.randint(0, 2)
    fires = rng.randint(1, 2) if rows * cols >= 4 else 1
    exits = rng.randint(1, 2) if rows * cols >= 5 else 1
    return [random_building(rng, rows, cols, 1, 5, fires, exits)]


def large(rng, index):
    size = 300
    if index == 0:
        # 불이 바로 뒤에서 쫓아오는 뱀 모양 통로: 대피에 4만 분 넘게 걸린다
        cells, last = snake(size, size)
        cells[0][0], cells[0][1] = "F", "S"
        cells[last[0]][last[1]] = "E"
        return [["".join(row) for row in cells]]
    # 아래쪽 절반에 불이 10,000곳 났고, 가운데 벽의 틈 세 곳으로 불이 위로 올라온다
    cells = [["#" if rng.chance(1, 5) else "." for _ in range(size)] for _ in range(size)]
    for c in range(size):
        cells[150][c] = "." if c in (30, 150, 270) else "#"
    placed = 0
    while placed < 10_000:
        r, c = rng.randint(151, size - 1), rng.randint(0, size - 1)
        if cells[r][c] == ".":
            cells[r][c] = "F"
            placed += 1
    cells[0][0] = "S"
    for r, c in ((0, 100), (140, 30), (149, size - 1)):  # 틈 가까운 두 비상구는 불이 먼저 닿는다
        cells[r][c] = "E"
    return [["".join(row) for row in cells]]
