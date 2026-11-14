LARGE = 2

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def vocabulary(rng, size, short, long):
    """서로 다른 제목 size개. 정렬해 두어 실행마다 같은 차례가 나온다."""
    words = set()
    while len(words) < size:
        words.add(rng.word(rng.randint(short, long), LETTERS))
    return sorted(words)


def small(rng):
    cases = [
        [["a"], 2],  # 가장 작은 입력: 꽂힌 책이 없다
        [["a", "a"], 2],  # 바로 k번째
        [["abcdefghij", "abcdefghij", "abcdefghij"], 100000],  # 가장 긴 제목, 가장 큰 k
        [["map", "map", "map", "map", "map"], 2],  # 같은 책이 k번보다 많이 빌려진다
        [["pine", "oak", "oak", "pine"], 2],  # 처음 나온 차례와 꽂힌 차례가 다르다
        [["zed", "ant", "zed", "ant"], 2],  # 사전 순과 꽂힌 차례가 다르다
        [["ab", "abc", "ab", "a", "abc", "a", "a"], 3],  # 앞부분이 같은 다른 제목
        [["moon", "sun", "star", "sun", "moon", "star", "moon", "sun"], 3],
        [["fig", "kiwi", "fig", "lime", "kiwi", "lime", "fig", "kiwi", "fig"], 4],
        [["x", "y", "z"], 3],  # 모두 한 번씩
    ]
    titles = ["ash", "elm", "fir", "yew", "oak"]
    for _ in range(6):
        cases.append([[rng.choice(titles) for _ in range(rng.randint(5, 30))], rng.randint(2, 6)])
    many = vocabulary(rng, 60, 1, 4)
    cases.append([[rng.choice(many) for _ in range(150)], 3])  # 제목이 많다
    return cases


def valid(loans, k):
    return (1 <= len(loans) <= 100_000 and 2 <= k <= 100_000
            and all(1 <= len(title) <= 10 and all("a" <= ch <= "z" for ch in title) for title in loans))


def random_small(rng):
    titles = ["a", "b", "c", "ab", "ba"]
    return [[rng.choice(titles) for _ in range(rng.randint(1, 12))], rng.randint(2, 4)]


def large(rng, index):
    if index == 0:
        # 서로 다른 제목이 3만 개: 목록에서 제목을 찾는 풀이도, 앞을 다시 세는 풀이도 오래 걸린다. 꽂히는 책은 몇백 권뿐이다
        words = vocabulary(rng, 30_000, 6, 10)
        return [[rng.choice(words) for _ in range(100_000)], 8]
    # 제목이 200개뿐이고 저마다 수백 번 빌려진다: 꽂히는 차례가 처음 나온 차례와 크게 다르다
    words = vocabulary(rng, 200, 3, 10)
    return [[rng.choice(words) for _ in range(100_000)], 500]
