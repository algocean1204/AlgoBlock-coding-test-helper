LARGE = 2


def expression(rng, n, low, high, weights):
    """수 n개(low ~ high)와 기호 n - 1개. weights는 ('+', '-', '^')가 나올 몫."""
    values = [rng.randint(low, high) for _ in range(n)]
    pool = "+" * weights[0] + "-" * weights[1] + "^" * weights[2]
    signs = "".join(rng.choice(pool) for _ in range(n - 1))
    return [values, signs]


def small(rng):
    cases = [
        [[5], ""],                      # 수 하나
        [[-100], ""],
        [[3, 8], "^"],
        [[-7, -2], "^"],
        [[8, 3], "-"],
        [[1, 2, 3], "-+"],
        [[1, 2, 3], "--"],
        [[4, 9, 1], "^^"],
        [[10, 1, 1, 1, 1], "----"],
        [[100] * 10, "+" * 9],          # 가장 큰 합
        [[-100] * 10, "+" * 9],         # 모두 음수: 시작값 0이면 틀린다
        [[-5, -3, -9, -1], "^^^"],
        [[7, 2, 5, 3], "-^-"],
        [[9, 5, 8, 6], "---"],
        [[1, -6, 4, 2, -3], "^-^+"],
        [[-100, 100, -100, 100, -100, 100, -100], "-^-^-^"],
    ]
    for _ in range(3):
        cases.append(expression(rng, rng.randint(6, 8), -100, 100, (1, 1, 1)))
    return cases


def random_small(rng):
    return expression(rng, rng.randint(1, 6), -9, 9, rng.choice([(1, 1, 1), (1, 2, 1), (0, 1, 1), (1, 0, 1)]))


def valid(values, signs):
    return (1 <= len(values) <= 150 and all(-100 <= x <= 100 for x in values)
            and len(signs) == len(values) - 1 and set(signs) <= {"+", "-", "^"})


def large(rng, index):
    if index == 0:
        return expression(rng, 150, -100, 100, (1, 1, 1))
    return expression(rng, 150, -100, 100, (1, 3, 1))  # '-'가 많아 최솟값이 자주 쓰인다
