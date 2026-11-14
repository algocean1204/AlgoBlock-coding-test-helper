LARGE = 2

POOL = ["rock", "jazz", "pop", "ballad", "trot", "hiphop", "folk", "indie"]
EXAMPLES = [["rock", "jazz", "rock"], ["pop", "pop", "pop", "jazz"], ["rock", "jazz", "pop", "rock"]]


def lineup(rng, counts):
    names = rng.sample(POOL, len(counts))
    genres = []
    for name, count in zip(names, counts):
        genres += [name] * count
    return rng.shuffle(genres)


def small(rng):
    # 정확성 케이스는 9팀까지(정의 그대로 풀이와 느린 풀이도 답은 맞게 끝나야 한다). 큰 팀 수는 medium과 효율성 케이스가 쓴다.
    cases = [
        ["indie"],                                          # 한 팀
        ["ballad", "ballad"],                               # 같은 장르 두 팀: 0
        ["jazz", "rock"],
        ["abcdefghij", "abcdefghij", "z"],                  # 가장 긴 장르 이름
        ["pop"] * 9,                                        # 모두 같다: 0
        ["trot", "folk"] * 4 + ["trot"],                    # 번갈아 놓는 한 가지뿐
        ["rock"] * 5 + ["jazz"] * 3,                        # 하나가 모자라 0
        ["rock"] * 4 + ["jazz"] * 3,                        # 딱 한 가지
        ["pop", "pop", "pop", "pop", "rock", "jazz", "rock"],
        ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
        ["rock", "rocks", "rock", "rocks", "rock"],         # 앞부분이 같은 다른 장르
        ["hiphop", "folk", "hiphop", "folk", "trot", "trot"],
    ]
    while len(cases) < 18:
        kinds = rng.randint(1, 3)
        counts = [rng.randint(1, 4) for _ in range(kinds)]
        if sum(counts) > 9:
            continue
        genres = lineup(rng, counts)
        if genres not in cases and genres not in EXAMPLES:
            cases.append(genres)
    return [[genres] for genres in cases]


def medium(rng):
    # 23팀까지. 모두 손으로 따질 수 있다.
    return [
        [["rock", "jazz"] * 11 + ["rock"]],                 # 12 + 11: 번갈아 놓는 한 가지
        [["pop", "folk"] * 10],                             # 10 + 10: 어느 쪽이 먼저인지 두 가지
        [["trot"] * 12 + ["indie"] * 9],                    # 12 + 9: 하나가 모자라 0
        [["ballad"] * 12 + ["jazz"] * 5 + ["pop"] * 6],     # ballad가 짝수 자리 12곳, 사이 11곳에 나머지: C(11, 5) = 462
    ]


def valid(genres):
    return (1 <= len(genres) <= 23 and len(set(genres)) <= 3
            and all(1 <= len(genre) <= 10 and genre.isalpha() and genre.islower() for genre in genres))


def random_small(rng):
    n = rng.randint(1, 8)
    letters = rng.choice(["ab", "abc", "abc"])
    return [[rng.choice(letters) for _ in range(n)]]


def large(rng, index):
    if index == 0:
        return [lineup(rng, [8, 8, 7])]  # 23팀을 가장 고르게 나눈 모양(답 1,118,268). 묶기만 하면 약 31억 가지를 끝까지 만든다
    return [lineup(rng, [8, 7, 6])]
