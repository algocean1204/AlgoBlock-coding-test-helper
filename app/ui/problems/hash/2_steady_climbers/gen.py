LARGE = 2

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def name_of(number):
    """0, 1, 2, …를 서로 다른 영문 소문자 이름으로(a, b, …, z, ba, bb, …)."""
    text = ""
    while True:
        text = LETTERS[number % 26] + text
        number //= 26
        if number == 0:
            return text


def pick(rng, count, people, step, limit):
    """people명이 섞여 들어오는 기록 count개. 날짜는 0~step일씩 늘어난다."""
    pool = [rng.word(rng.randint(1, 3), "abcde") for _ in range(people)]
    names = [rng.choice(pool) for _ in range(count)]
    days, day = [], rng.randint(1, 5)
    for _ in range(count):
        day += rng.randint(0, step)
        days.append(day)
    return [names, days, limit]


def small(rng):
    cases = [
        [["a"], [1], 1],  # 기록 하나
        [["a", "a"], [5, 5], 1],  # 같은 날 두 번: 하루만 왔다
        [["a", "a"], [5, 6], 1],  # 차이가 limit과 같다
        [["a", "a"], [5, 7], 1],  # 차이가 limit을 넘는다
        [["a", "a", "a"], [1, 2, 1000000], 999998],  # 마지막 차이만 넘는다
        [["a", "a", "a"], [1, 9, 10], 3],  # 처음 차이만 넘는다: 마지막 차이만 보면 틀린다
        [["a", "a", "a", "a"], [1, 3, 5, 7], 2],  # 처음 날과의 차이는 limit을 넘지만 이웃끼리는 괜찮다
        [["x", "y", "x", "y", "x", "y"], [1, 1, 2, 2, 3, 3], 1],  # 둘이 번갈아 날마다 온다
        [["p", "q", "r"], [1, 2, 3], 1000000],  # 모두 하루씩만 왔다
        [["solo", "solo", "solo", "duo", "duo"], [4, 4, 4, 4, 9], 5],
        [["zzzzzzzzzz", "zzzzzzzzzz"], [1, 1000000], 1000000],  # 가장 큰 값
        [["m", "n", "m", "m", "n", "n", "m"], [2, 3, 3, 3, 8, 8, 9], 5],
    ]
    for _ in range(6):
        cases.append(pick(rng, rng.randint(6, 20), rng.randint(2, 5), rng.randint(0, 3), rng.randint(1, 4)))
    return cases


def random_small(rng):
    return pick(rng, rng.randint(1, 12), rng.randint(1, 4), rng.randint(0, 3), rng.randint(1, 4))


def large(rng, index):
    count = 100_000
    if index == 0:  # 손님 50,000명이 섞여 두 번씩 온다: 이름이 많다
        names = [name_of(number % 50_000) for number in range(count)]
        rng.shuffle(names)
        days = sorted(rng.randint(1, 1_000_000) for _ in range(count))
        return [names, days, 20_000]
    # 손님 30,000명, 날마다 여럿이 온다. 같은 날 다시 들어온 기록이 섞인다
    names = [name_of(rng.randint(0, 29_999)) for _ in range(count)]
    days, day = [], 1
    for _ in range(count):
        day += rng.choice([0, 0, 0, 1, 2, 5, 30])
        days.append(min(day, 1_000_000))
    return [names, days, 3_000]


def valid(names, days, limit):
    return (1 <= len(names) == len(days) <= 100_000
            and all(1 <= len(name) <= 10 and name.isascii() and name.isalpha() and name.islower() for name in names)
            and all(1 <= day <= 1_000_000 for day in days)
            and all(days[k] <= days[k + 1] for k in range(len(days) - 1))
            and 1 <= limit <= 1_000_000)
