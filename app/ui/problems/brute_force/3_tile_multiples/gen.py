LARGE = 2

EXAMPLES = [["305", 5], ["444", 4], ["507", 7]]


def small(rng):
    # 정확성 케이스는 5장까지(느린 풀이도 답은 맞게 끝나야 한다). 6~8장은 medium과 효율성 케이스가 쓴다.
    cases = [
        ["00", 2],       # 맨 앞에 0을 놓을 수밖에 없어 만들 수 있는 수가 없다
        ["10", 2],       # 10 하나뿐
        ["05", 5],       # 05는 만들 수 없다: 50 하나
        ["11", 1000],    # 가장 큰 m: 배수가 없다
        ["12", 2],
        ["77", 7],       # 같은 수를 두 방법으로 만든다
        ["00000", 2],
        ["10000", 2],    # 1 뒤에 0을 붙인 10, 100, 1000, 10000
        ["11111", 11],   # 11, 1111
        ["12345", 3],
        ["98765", 13],
        ["50505", 5],
        ["30303", 3],
        ["13579", 2],    # 짝수가 없다
    ]
    while len(cases) < 18:
        args = [rng.word(rng.randint(3, 5), rng.choice(["0123456789", "01379", "1133", "05"])), rng.choice([2, 3, 4, 5, 6, 7, 9, 11, 25, 37])]
        if args not in cases and args not in EXAMPLES:
            cases.append(args)
    return cases


def medium(rng):
    # 여덟 장에서만 드러나는 실수를 '틀림'으로 잡는다. 앞의 셋은 손으로 따질 수 있다.
    return [
        ["11111111", 11],   # 짝수 자리의 11, 1111, 111111, 11111111: 4
        ["10000000", 2],    # 10, 100, …, 10000000: 7
        ["22222222", 2],    # 22부터 22222222까지 7개
        ["12345678", 9],
        ["90876501", 7],
    ]


def valid(tiles, m):
    return 2 <= len(tiles) <= 8 and all(ch in "0123456789" for ch in tiles) and 2 <= m <= 1000


def random_small(rng):
    return [rng.word(rng.randint(2, 4), rng.choice(["0123456789", "01379", "0123", "05"])), rng.choice([2, 3, 4, 5, 7, 11])]


def large(rng, index):
    if index == 0:  # 서로 다른 숫자 여덟 장(0 포함): 서로 다른 수가 9만 개를 넘는다
        chosen = ["0"] + rng.sample(list("123456789"), 7)
        return ["".join(rng.shuffle(chosen)), 7]
    chosen = rng.sample(list("123456789"), 8)  # 0이 없는 여덟 장
    return ["".join(rng.shuffle(chosen)), rng.choice([11, 13, 17])]
