LARGE = 0


def names(rng, count, letters, longest):
    seen = []
    while len(seen) < count:
        name = rng.word(rng.randint(1, longest), letters)
        if name not in seen:
            seen.append(name)
    return seen


def medals_for(rng, count, high):
    return [[rng.randint(0, high), rng.randint(0, high), rng.randint(0, high)] for _ in range(count)]


def small(rng):
    cases = [
        [["a"], [[0, 0, 0]]],  # 가장 작은 입력
        [["zz", "a"], [[100, 100, 100], [100, 100, 100]]],  # 가장 큰 값이 모두 같다: 이름 순
        [["abc", "ab", "a", "b"], [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]]],  # 앞부분이 같은 이름
        [["x", "y", "z"], [[3, 0, 0], [2, 9, 9], [1, 0, 0]]],  # 이미 순위대로 들어온 입력
        [["c", "b", "a"], [[5, 1, 0], [5, 2, 0], [5, 3, 0]]],  # 금메달이 같고 은메달로 갈린다(입력과 반대 순서)
        [["p", "q"], [[1, 0, 0], [0, 50, 50]]],  # 총합은 q가 많지만 금메달이 앞선다
        [["bb", "aa"], [[2, 2, 1], [2, 2, 0]]],  # 동메달로만 갈린다
        [["dd", "cc", "bb", "aa"], [[0, 0, 0], [0, 0, 1], [0, 1, 0], [1, 0, 0]]],  # 메달 한 개씩, 순위가 입력과 반대
        [["d", "c", "b", "a"], [[1, 0, 0], [0, 100, 0], [0, 1, 0], [0, 0, 100]]],  # 100개가 윗 메달 1개를 넘지 못한다: 100씩 곱해 합치면 틀린다
    ]
    cases.append([names(rng, 50, "abcdefghijklmnopqrstuvwxyz", 10), medals_for(rng, 50, 100)])  # 가장 큰 입력
    cases.append([names(rng, 50, "abc", 4), medals_for(rng, 50, 1)])  # 가장 큰 입력, 동점이 많다
    for _ in range(6):
        n = rng.randint(5, 30)
        cases.append([names(rng, n, "abc", 4), medals_for(rng, n, 2)])
    return cases


def random_small(rng):
    n = rng.randint(1, 7)
    return [names(rng, n, "ab", 3), medals_for(rng, n, 2)]


def large(rng, index):
    return []
