LARGE = 0


def small(rng):
    cases = [
        [1, 1, [0, 0], "N"],                          # 가장 작은 주차장, 첫 명령부터 밖
        [1, 1, [0, 0], "NSWENSWE"],                   # 모두 건너뛴다
        [2, 2, [0, 0], "NES"],                        # 건너뛴 뒤에도 이어서 실행
        [2, 3, [1, 2], "SEN"],                        # 오른쪽 아래 모서리에서 한 칸 밖
        [1, 5, [0, 0], "EEEEEEEEW"],                  # 끝에 닿은 뒤 계속 밀기
        [5, 1, [4, 0], "NNNNNNNNNS"],
        [3, 7, [2, 6], "SESEWWN"],                    # 세로보다 가로가 긴 주차장
        [7, 3, [0, 2], "EEEESSSSSSSSSWWW"],           # 가로보다 세로가 긴 주차장
        [4, 6, [0, 0], "NNNN"],                       # 위로만 밀기
        [6, 4, [5, 3], "SSSSEEEE"],                   # 아래·오른쪽으로만 밀기
        [100, 100, [0, 0], "S" * 120 + "E" * 120],    # 가장 큰 주차장의 모서리
        [100, 1, [0, 0], "S" * 99 + "SN"],
        [2, 100, [1, 99], "E" + "W" * 50 + "N" + "N"],
    ]
    for _ in range(5):
        rows, cols = rng.randint(2, 9), rng.randint(2, 9)
        start = [rng.randint(0, rows - 1), rng.randint(0, cols - 1)]
        cases.append([rows, cols, start, rng.word(rng.randint(20, 60), "NSWE")])
    rows, cols = rng.randint(30, 100), rng.randint(30, 100)
    cases.append([rows, cols, [rng.randint(0, rows - 1), rng.randint(0, cols - 1)], rng.word(1000, "NNSSWWEESE")])
    return cases


def valid(rows, cols, start, commands):
    return (1 <= rows <= 100 and 1 <= cols <= 100 and len(start) == 2
            and 0 <= start[0] < rows and 0 <= start[1] < cols
            and 1 <= len(commands) <= 1000 and set(commands) <= set("NSWE"))


def random_small(rng):
    rows, cols = rng.randint(1, 4), rng.randint(1, 4)
    start = [rng.randint(0, rows - 1), rng.randint(0, cols - 1)]
    return [rows, cols, start, rng.word(rng.randint(1, 12), "NSWE")]


def large(rng, index):
    return []
