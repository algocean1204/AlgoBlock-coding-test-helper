LARGE = 2


def random_garden(rng, rows, cols, rock):
    """rock/10의 확률로 바위. 출발 칸 'S'를 잔디 칸 하나에 놓는다."""
    cells = [['#' if rng.chance(rock, 10) else '.' for _ in range(cols)] for _ in range(rows)]
    r, c = rng.randint(0, rows - 1), rng.randint(0, cols - 1)
    cells[r][c] = 'S'
    return [''.join(line) for line in cells]


def small(rng):
    cases = [
        [["S"], "FLFRFF"],                                  # 칸이 하나뿐
        [["S"], "L"],                                       # 움직이지 않는다
        [[".S."], "RFFFLLFFFF"],                            # 한 줄짜리 정원
        [["#", "S", "."], "FFLLFF"],                        # 위는 바위, 돌아서 아래로
        [["###", "#S#", "###"], "FRFRFRFRF"],               # 바위에 둘러싸였다
        [["S...", "....", "...."], "RFFFRFFLLFFRRFF"],      # 같은 길을 되돌아간다
        [["....", "..S.", "...."], "LFFRFRFFFRFFFRFF"],     # 출발 칸으로 돌아오지 않는다
        [["S....", "####.", ".....", ".####", "....."], "RFFFFRFFRFFFFLFFLFFFF"],  # 구불구불한 길
        [[".....", ".#.#.", "..S..", ".#.#.", "....."], "LLLFRRRFLFFRFF"],  # 왼쪽 세 번 = 오른쪽 한 번
        [["..#..", "..#..", "S.#..", "..#.."], "RFFFFFLFFFFRRFFFFFF"],   # 바위 벽에 막힌다
        [["." * 12 for _ in range(3)] + ["." * 11 + "S"], "LFFFFFFFFFFFFFRRFFFFFFFFFFFFF"],
    ]
    for _ in range(6):
        rows, cols = rng.randint(3, 10), rng.randint(3, 10)
        cases.append([random_garden(rng, rows, cols, 2), rng.word(rng.randint(30, 80), "LRFFFF")])
    cases.append([random_garden(rng, 20, 20, 1), rng.word(1000, "LRFFFFFF")])
    return cases


def valid(garden, commands):
    width = len(garden[0]) if garden else 0
    return (1 <= len(garden) <= 200 and 1 <= width <= 200 and all(len(line) == width for line in garden)
            and all(set(line) <= set(".#S") for line in garden) and sum(line.count('S') for line in garden) == 1
            and 1 <= len(commands) <= 100_000 and set(commands) <= set("LRF"))


def random_small(rng):
    return [random_garden(rng, rng.randint(1, 4), rng.randint(1, 4), 3), rng.word(rng.randint(1, 15), "LRFFF")]


def large(rng, index):
    size = 200
    if index == 0:  # 왼쪽 아래에서 출발해 열마다 위아래로 훑어 4만 칸을 모두 지난 뒤, 이미 지난 칸을 계속 돌아다닌다
        garden = ['.' * size for _ in range(size - 1)] + ['S' + '.' * (size - 1)]
        parts = []
        for col in range(size):
            parts.append('F' * (size - 1))
            if col < size - 1:
                parts.append('RFR' if col % 2 == 0 else 'LFL')
        sweep = ''.join(parts)
        return [garden, sweep + rng.word(100_000 - len(sweep), "LRFFFFFF")]
    # 행 방향으로 뱀처럼 훑어 4만 칸을 다 깎은 뒤, 목록 맨 끝에 붙은 맨 아랫줄만 왕복한다(목록에서 찾으면 매번 끝까지 훑는다)
    garden = ['S' + '.' * (size - 1)] + ['.' * size for _ in range(size - 1)]
    parts = ['R']
    for row in range(size):
        parts.append('F' * (size - 1))
        if row < size - 1:
            parts.append('RFR' if row % 2 == 0 else 'LFL')
    sweep = ''.join(parts)
    return [garden, (sweep + ('LL' + 'F' * (size - 1)) * 1000)[:100_000]]
