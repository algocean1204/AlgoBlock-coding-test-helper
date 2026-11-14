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


def pick(rng, count, shapes, high):
    """모양 shapes가지 가운데서 부스 count곳, 걸리는 시간 1~high, time은 합의 일부."""
    names = [rng.word(rng.randint(1, 4), "abcdefgh") for _ in range(shapes)]
    kinds = [rng.choice(names) for _ in range(count)]
    minutes = [rng.randint(1, high) for _ in range(count)]
    time = rng.randint(1, max(1, sum(minutes) * 2 // 3))
    return [kinds, minutes, time]


def small(rng):
    cases = [
        [["a"], [5], 5],  # 부스 하나: 시간이 꼭 맞는다
        [["a"], [5], 4],  # 부스 하나: 모자란다
        [["a", "a", "a"], [3, 1, 2], 100],  # 모두 같은 모양: 한 칸
        [["x", "y", "z"], [10000, 10000, 10000], 1000000000],  # 모두 받는다
        [["x", "y", "z"], [4, 4, 4], 8],  # 합이 time과 꼭 같다
        [["p", "q", "p", "q"], [9, 9, 1, 1], 2],  # 뒤에 나온 짧은 부스를 남겨야 한다
        [["m", "n", "o", "p"], [8, 1, 2, 3], 6],  # 정렬해야 한다: 처음 것이 길다
        [["k", "k", "j", "i"], [1, 1, 1, 1], 3],  # 같은 모양을 두 번 세면 넘게 센다
        [["long", "short"], [7, 2], 1],  # 아무것도 못 받는다
        [["aa", "ab", "ac", "aa", "ab"], [6, 5, 4, 3, 2], 9],
        [["s", "t", "u", "v", "w", "s"], [2, 3, 3, 3, 3, 1], 10],
        [["q"] * 5 + ["r"], [1, 2, 3, 4, 5, 2], 3],
    ]
    for _ in range(6):
        cases.append(pick(rng, rng.randint(4, 10), rng.randint(2, 7), rng.randint(5, 30)))
    return cases


def random_small(rng):
    return pick(rng, rng.randint(1, 9), rng.randint(1, 6), rng.randint(3, 12))


def large(rng, index):
    count = 100_000
    numbers = rng.shuffle(list(range(count)))
    if index == 0:  # 모양이 모두 다르고 시간이 넉넉하다: 거의 모든 칸을 채운다
        kinds = [name_of(number) for number in numbers]
        minutes = [rng.randint(1, 10_000) for _ in range(count)]
        return [kinds, minutes, sum(minutes) * 9 // 10]
    # 모양 60,000가지, 같은 모양이 섞인다: 절반쯤 채운다
    kinds = [name_of(number % 60_000) for number in numbers]
    minutes = [rng.randint(1, 10_000) for _ in range(count)]
    return [kinds, minutes, 150_000_000]


def valid(kinds, minutes, time):
    return (1 <= len(kinds) == len(minutes) <= 100_000
            and all(1 <= len(kind) <= 10 and kind.isascii() and kind.isalpha() and kind.islower() for kind in kinds)
            and all(1 <= minute <= 10_000 for minute in minutes)
            and 1 <= time <= 1_000_000_000)
