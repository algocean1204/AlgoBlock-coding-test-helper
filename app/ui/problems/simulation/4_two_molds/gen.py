LARGE = 2


def random_dish(rng, n, m, mold, wall):
    """칸마다 mold/10의 확률로 'A'나 'B', wall/10의 확률로 '#', 나머지는 빈칸."""
    cells = []
    for _ in range(n):
        row = ''
        for _ in range(m):
            roll = rng.randint(0, 9)
            row += rng.choice("AB") if roll < mold else '#' if roll < mold + wall else '.'
        cells.append(row)
    return cells


def snake(n, m):
    """짝수 행은 통로, 홀수 행은 벽이고 오른쪽 끝과 왼쪽 끝이 번갈아 뚫린 구불구불한 길. 길 양 끝에 'A'와 'B'."""
    cells = [['.'] * m if r % 2 == 0 else ['#'] * m for r in range(n)]
    for r in range(1, n, 2):
        cells[r][m - 1 if r % 4 == 1 else 0] = '.'
    cells[0][0] = 'A'
    last = n - 1 if n % 2 == 1 else n - 2
    cells[last][0 if last % 4 == 2 else m - 1] = 'B'
    return [''.join(row) for row in cells]


def one_side(n, m):
    """구불구불한 길을 'A' 쪽 한 끝에서만 채운다."""
    return [line.replace('B', '.') for line in snake(n, m)]


def small(rng):
    cases = [
        [["A"], 1],                                   # 가장 작은 접시
        [["."], 5],                                   # 균이 없다
        [["A.B"], 1],                                 # 1 대 1: '#'
        [["A......."], 3],                            # 제자리에서 바꾸면 한 시간에 끝까지 퍼진다
        [["ABA", "BAB", "ABA"], 1],                   # 번식에서 바뀌는 칸이 없어도 포위는 한다
        [["....", "....", "...."], 4],                # 맞닿은 균이 없으면 빈칸 그대로
        [["#A#", "B.B", "#A#"], 2],                   # 2 대 2: '#'
        [[".B.", "B.A", "..."], 1],                   # 2 대 1: 'B'
        [["B.B", "A..", "B.B"], 3],                   # 방금 자란 칸이 같은 시간에 둘러싸인다(2단계는 1단계가 끝난 판을 본다)
        [[".BA.", ".AB.", ".BA."], 1],                # 둘러싸인 두 칸이 동시에 '#'
        [["BAB", ".B."], 2],                          # 처음부터 둘러싸인 칸
        [snake(9, 9), 13],                            # 구불구불한 길의 중간 모습
        [snake(9, 9), 1000],
        [one_side(30, 30), 1000],                     # 한쪽 끝에서만 채워 460시간 넘게 바뀐다
        [one_side(27, 30), 999],
        # 균이 빽빽해 1단계에서 자란 칸 때문에 2단계에서 둘러싸이는 칸이 여럿 생긴다(단계의 순서·기준 판 실수가 드러난다)
        [["B...B.", ".AA#B#", "A..#A.", "BBAB..", "BAB.A.", ".#AB.A"], 2],
        [[".BBA..A", ".ABA..B", ".....A.", "B#.A.BA", "BBBB...", "...ABAB", "AABAA.."], 5],
        [[".A.AB.A.", "AABABB.B", "A.BB.#.A", "ABB.#B..", ".B#BA.AA", "B.B..B#B"], 2],
    ]
    n, m = rng.randint(4, 12), rng.randint(4, 12)
    cases.append([random_dish(rng, n, m, 4, 1), rng.randint(1, 6)])
    cases.append([random_dish(rng, 30, 30, 2, 2), 1000])
    return cases


def valid(dish, hours):
    m = len(dish[0]) if dish else 0
    return (1 <= len(dish) <= 30 and 1 <= m <= 30 and all(len(line) == m for line in dish)
            and all(set(line) <= set(".AB#") for line in dish) and 1 <= hours <= 1_000_000_000)


def random_small(rng):
    return [random_dish(rng, rng.randint(1, 5), rng.randint(1, 5), rng.randint(2, 6), rng.randint(0, 2)), rng.randint(1, 8)]


def large(rng, index):
    if index == 0:  # 길이 460칸이 넘는 길을 한쪽 끝에서만 채워 460시간 넘게 바뀐다
        return [one_side(30, 30), 1_000_000_000]
    return [random_dish(rng, 30, 30, 2, 2), rng.randint(900_000_000, 1_000_000_000)]
