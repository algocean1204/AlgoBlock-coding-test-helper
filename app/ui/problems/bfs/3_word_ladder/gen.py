LARGE = 2


def valid(start, goal, dictionary):
    words = [start, goal] + dictionary
    if start == goal or not 1 <= len(dictionary) <= 100_000 or len(set(dictionary)) != len(dictionary):
        return False
    return all(len(w) == len(start) and w.isalpha() and w.islower() and w.isascii() for w in words) and 1 <= len(start) <= 6


def random_case(rng, length, letters, size, goal_inside):
    """letters로 만든 길이 length의 서로 다른 낱말 size개. goal_inside면 goal을 사전에 넣는다."""
    words = set()
    while len(words) < size:
        words.add(rng.word(length, letters))
    dictionary = rng.shuffle(sorted(words))
    goal = rng.choice(dictionary) if goal_inside else rng.word(length, letters)
    start = goal
    while start == goal:  # start는 사전 안에서 고르기도, 밖에서 만들기도 한다
        start = rng.choice(dictionary) if len(dictionary) > 1 and rng.chance(1, 2) else rng.word(length, letters)
    return [start, goal, dictionary]


def small(rng):
    cases = [
        ["a", "b", ["b"]],  # 한 글자 낱말
        ["a", "b", ["c"]],
        ["ab", "cd", ["ad", "cd"]],
        ["abc", "abd", ["abd", "abc"]],  # start도 사전에 있다
        ["cat", "dog", ["cot", "cog", "dog"]],
        ["aab", "abb", ["abb"]],  # 글자 집합은 같지만 한 자리만 다르다
        ["abc", "bca", ["bca", "bbc", "bcc"]],  # 글자 집합이 같아도 세 자리가 다르다
        ["aaa", "bba", ["aab", "bab", "bbb", "bba"]],  # 끝 글자를 바꿨다가 되돌린다
        ["abc", "xyz", ["abd", "xyz", "xbc"]],  # goal이 사전에 있지만 닿지 않는다
        ["star", "stay", ["scar", "soar"]],  # goal이 사전에 없다
        ["abc", "abz", ["xbc", "xbz", "abz"]],  # 사전 앞쪽부터 따라가면 멀리 돈다
        ["fold", "mild", ["mold", "bold", "bald", "bale", "male", "mile", "mild", "gold"]],
        ["aaaa", "bbbb", ["baaa", "caaa", "cbaa", "cbba", "cbbb", "bbbb"]],  # goal을 닮은 baaa로 먼저 가면 돌아 나와야 한다
    ]
    cases.append(random_case(rng, 3, "abc", 14, True))
    cases.append(random_case(rng, 3, "abcd", 30, True))
    cases.append(random_case(rng, 4, "abcd", 80, True))
    cases.append(random_case(rng, 4, "abcde", 120, True))
    cases.append(random_case(rng, 2, "abcdefgh", 20, True))
    cases.append(random_case(rng, 5, "ab", 20, False))
    return cases


def random_small(rng):
    length = rng.randint(1, 3)
    letters = rng.choice(["ab", "abc", "abc"])
    size = rng.randint(1, min(10, len(letters) ** length))
    return random_case(rng, length, letters, size, rng.chance(3, 4))


def large(rng, index):
    if index == 0:
        # a~h로만 만든 낱말 99,999개가 촘촘히 이어져 있고, goal은 이웃이 하나도 없다: 닿는 낱말을 모두 본 뒤에야 -1을 안다
        words = set()
        while len(words) < 99_999:
            words.add(rng.word(6, "abcdefgh"))
        dictionary = sorted(words)
        start = rng.choice(dictionary)
        return [start, "zzzzzz", rng.shuffle(dictionary + ["zzzzzz"])]
    # 한 글자씩 바꿔 가며 10만 걸음을 걷는다: 걸음 사이에 지름길이 생겨 답은 걸음 수보다 훨씬 작다
    walk = [rng.word(6)]
    used = {walk[0]}
    while len(walk) < 100_000:
        word = walk[-1]
        i = rng.randint(0, 5)
        candidate = word[:i] + rng.choice("abcdefghijklmnopqrstuvwxyz") + word[i + 1:]
        if candidate not in used:
            used.add(candidate)
            walk.append(candidate)
    return [walk[0], walk[-1], rng.shuffle(list(walk))]
