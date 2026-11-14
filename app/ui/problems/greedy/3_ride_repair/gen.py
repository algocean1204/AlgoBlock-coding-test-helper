LARGE = 2


def pick(rng, count, fix_high, line_high, walk_high):
    fix = [rng.randint(1, fix_high) for _ in range(count)]
    line = [rng.randint(0, line_high) for _ in range(count)]
    return [fix, line, rng.randint(0, walk_high)]


def small(rng):
    cases = [
        [[7], [3], 50],  # 한 대: 걷지 않는다
        [[7], [0], 0],  # 손님이 없다
        [[1000, 1000], [100, 100], 1000],  # 가장 큰 값
        [[3, 3, 3], [2, 2, 2], 5],  # 모두 같다
        [[1, 9], [1, 10], 0],  # 짧은 것부터 하면 손해
        [[8, 1], [5, 1], 0],  # 손님이 많은 것부터 하면 손해
        [[1, 12], [1, 11], 15],  # 걷는 시간을 빼면 차례가 뒤집힌다
        [[2, 4, 1], [0, 0, 0], 3],  # 손님이 아무도 없다
        [[5, 1, 3], [0, 2, 0], 2],  # 손님이 0명인 놀이기구가 섞인다
        [[6, 2, 4, 3], [3, 1, 2, 1], 0],  # 비율이 같은 것들(6/3, 2/1, 4/2)
        [[1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1], 1],
        [[9, 2, 7, 4, 5, 1], [1, 0, 4, 2, 8, 0], 6],
    ]
    for _ in range(6):
        cases.append(pick(rng, rng.randint(3, 7), rng.randint(3, 30), rng.randint(1, 20), rng.choice([0, 3, 10, 50])))
    return cases


def random_small(rng):
    return pick(rng, rng.randint(1, 6), rng.randint(2, 8), rng.randint(1, 5), rng.choice([0, 1, 2, 5, 9]))


def medium(rng):
    count = 150  # 기다림의 합이 int(2,147,483,647)를 넘는다
    return [
        [[1000] * count, [100] * count, 1000],
        [[1000 - k % 3 for k in range(count)], [100 - k % 2 for k in range(count)], 1000],  # 비율이 조금씩 다르다
    ]


def large(rng, index):
    count = 100_000
    if index == 0:
        return pick(rng, count, 1000, 100, 1000)
    # 가장 큰 값 가까이: 끝나는 시각과 손님 수가 커서 합이 int를 크게 넘는다
    fix = [rng.randint(900, 1000) for _ in range(count)]
    line = [rng.randint(0, 100) for _ in range(count)]
    return [fix, line, 1000]


def valid(fix, line, walk):
    return (1 <= len(fix) == len(line) <= 100_000 and all(1 <= value <= 1000 for value in fix)
            and all(0 <= value <= 100 for value in line) and 0 <= walk <= 1000)
