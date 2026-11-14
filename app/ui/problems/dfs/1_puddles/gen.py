LARGE = 0


def snake(rows, cols):
    """한 줄로 길게 이어진 웅덩이 하나(짝수 줄은 꽉 차고, 홀수 줄은 양 끝을 번갈아 잇는다)."""
    grid = []
    for r in range(rows):
        if r % 2 == 0:
            grid.append("#" * cols)
        elif r % 4 == 1:
            grid.append("." * (cols - 1) + "#")
        else:
            grid.append("#" + "." * (cols - 1))
    return grid


def random_grid(rng, rows, cols, wet):
    return ["".join("#" if rng.chance(wet, 10) else "." for _ in range(cols)) for _ in range(rows)]


def small(rng):
    cases = [
        [["."]],
        [["#"]],
        [["#", ".", "#"]],  # 위아래 끝 칸: -1번이 반대쪽 끝을 가리키면 하나로 이어진다
        [["#.#"]],  # 왼쪽 끝과 오른쪽 끝
        [["#.", ".#"]],  # 대각선으로만 맞닿았다
        [["##", "##"]],
        [["#.#.#", "#.#.#", "#####"]],  # 빗 모양: 아래쪽에서만 이어진다
        [["#####", "#...#", "#.#.#", "#...#", "#####"]],  # 고리 안에 따로 떨어진 칸
        [[".#.#.", "#.#.#", ".#.#.", "#.#.#"]],  # 체크무늬: 모두 대각선으로만 맞닿았다
        [["." * 30] * 30],  # 물이 없다
        [["#" * 30] * 30],  # 모두 물: 한 덩어리(가장 큰 크기)
        [snake(30, 30)],
        [["#" * 30]],
        [["#.." * 9 + "#"] * 3],
    ]
    for wet in (3, 4, 5, 6):
        cases.append([random_grid(rng, rng.randint(8, 25), rng.randint(8, 25), wet)])
    return cases


def random_small(rng):
    return [random_grid(rng, rng.randint(1, 6), rng.randint(1, 6), rng.randint(2, 7))]


def valid(floor):
    return (1 <= len(floor) <= 30 and 1 <= len(floor[0]) <= 30
            and all(len(row) == len(floor[0]) and set(row) <= set("#.") for row in floor))


def large(rng, index):
    return []
