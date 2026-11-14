LARGE = 3


def snake(rows, cols):
    """모든 칸을 한 줄로 지나 밖으로 나가는 길: 짝수 줄은 오른쪽으로, 홀수 줄은 왼쪽으로 가고 줄 끝에서 내려간다."""
    return ["R" * (cols - 1) + "D" if r % 2 == 0 else "D" + "L" * (cols - 1) for r in range(rows)]


def ring(rows, cols):
    """모든 칸을 한 바퀴 도는 고리(rows는 짝수, cols는 2 이상). 맨 윗줄을 오른쪽으로 가고, 1열부터 끝 열 사이를
    지그재그로 내려간 뒤, 0열을 따라 올라온다."""
    grid = [[""] * cols for _ in range(rows)]
    for c in range(cols - 1):
        grid[0][c] = "R"
    grid[0][cols - 1] = "D"
    for r in range(1, rows):
        grid[r][0] = "U"
        if r % 2 == 1:
            for c in range(2, cols):
                grid[r][c] = "L"
            grid[r][1] = "D" if r < rows - 1 else "L"
        else:
            for c in range(1, cols - 1):
                grid[r][c] = "R"
            grid[r][cols - 1] = "D"
    return ["".join(row) for row in grid]


def feeding(rng, rows, cols):
    """왼쪽 절반은 큰 고리, 오른쪽 절반은 대부분 왼쪽(고리 쪽)을 가리켜 길게 들어오는 꼬리가 많다."""
    left = ring(rows, cols // 2)
    right_width = cols - cols // 2
    return [left[r] + "".join("L" if rng.chance(3, 4) else rng.choice("UDR") for _ in range(right_width)) for r in range(rows)]


def random_board(rng, rows, cols, letters="UDLR"):
    return ["".join(rng.choice(letters) for _ in range(cols)) for _ in range(rows)]


def small(rng):
    cases = [
        [["U"]],
        [["RL"]],
        [["RRRL"]],  # 꼬리 두 칸이 길이 2인 고리로 들어간다
        [["DL", "RU"]],
        [["R" * 40]],
        [["D"] * 40],
        [snake(30, 30)],  # 900칸이 한 줄: 재귀는 900번 깊어진다
        [ring(30, 30)],  # 900칸이 한 고리: 모든 칸이 900점
        [feeding(rng, 30, 30)],
        [["RRRRRRRRRD", "ULLLLLLLLL"] + ["U" * 10] * 8],  # 아래 줄들은 고리로 길게 들어온다
    ]
    for rows, cols, letters in ((5, 5, "UDLR"), (8, 12, "UDLR"), (15, 15, "UDLR"), (20, 20, "UDLR"), (12, 20, "RLD"), (20, 12, "UDR"), (25, 25, "UDLR")):
        cases.append([random_board(rng, rows, cols, letters)])
    return cases


def random_small(rng):
    return [random_board(rng, rng.randint(1, 5), rng.randint(1, 5), rng.choice(["UDLR", "UDLR", "RLD", "UDR", "RL"]))]


def large(rng, index):
    if index == 0:  # 25만 칸이 한 줄로 이어져 밖으로 나간다: 칸마다 따로 걸으면 약 300억 번, 재귀는 25만 번 깊어진다
        return [snake(500, 500)]
    if index == 1:  # 25만 칸이 한 고리: 모든 칸이 25만 점, 합은 625억(int를 넘는다)
        return [ring(500, 500)]
    return [feeding(rng, 500, 500)]


def valid(board):
    return (1 <= len(board) <= 500 and 1 <= len(board[0]) <= 500
            and all(len(row) == len(board[0]) and set(row) <= set("UDLR") for row in board))
