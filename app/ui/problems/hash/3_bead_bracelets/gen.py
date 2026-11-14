LARGE = 2


def turn(rng, beads):
    """같은 팔찌를 다른 구슬부터, 때로는 반대 방향으로 읽은 문자열."""
    if rng.chance(1, 2):
        beads = beads[::-1]
    start = rng.randint(0, len(beads) - 1)
    return beads[start:] + beads[:start]


def pick(rng, count, designs, longest, letters):
    """디자인 designs개를 만들어 두고, 그 가운데서 골라 돌리고 뒤집어 적은 팔찌 count개."""
    pool = [rng.word(rng.randint(1, longest), letters) for _ in range(designs)]
    return [[turn(rng, rng.choice(pool)) for _ in range(count)]]


def small(rng):
    cases = [
        [["a"]],  # 팔찌 하나
        [["z", "z", "z"]],  # 모두 같은 문자열
        [["ab", "ba"]],  # 구슬 둘
        [["abcd", "dcba"]],  # 뒤집기만
        [["abcd", "bcda", "cdab", "dabc"]],  # 돌리기만
        [["abcd", "badc", "cbad", "adcb"]],  # 뒤집은 것을 돌린 모습들
        [["abcd", "abdc", "acbd", "acdb", "adbc"]],  # 색의 개수는 같지만 디자인이 다르다
        [["a", "aa", "aaa", "aa", "a", "aa"]],  # 구슬 수가 다르면 다른 디자인
        [["aabb", "abab", "baba", "bbaa", "abba"]],  # 색이 같은 둘씩: 두 디자인
        [["abcdefghij", "jihgfedcba", "fghijabcde", "abcdefghji"]],  # 가장 긴 팔찌
        [["xyz", "xzy", "yxz", "q", "q", "q"]],  # 디자인 하나에 셋, 다른 디자인에 셋
        [["aab", "aba", "baa", "abb", "bab", "bba", "bba"]],
    ]
    for _ in range(6):
        cases.append(pick(rng, rng.randint(6, 16), rng.randint(2, 6), rng.randint(3, 8), "abc"))
    return cases


def random_small(rng):
    return pick(rng, rng.randint(1, 10), rng.randint(1, 5), rng.randint(1, 6), rng.choice(["ab", "abc", "abcd"]))


def large(rng, index):
    count = 100_000
    if index == 0:  # 구슬 10개, 색 4가지: 디자인이 아주 많다
        return [[rng.word(10, "abcd") for _ in range(count)]]
    # 디자인 40,000개를 돌리고 뒤집어 적는다: 같은 디자인이 여러 모습으로 섞인다
    return pick(rng, count, 40_000, 10, "abcdefgh")


def valid(bracelets):
    return (1 <= len(bracelets) <= 100_000
            and all(1 <= len(beads) <= 10 and beads.isascii() and beads.isalpha() and beads.islower() for beads in bracelets))
