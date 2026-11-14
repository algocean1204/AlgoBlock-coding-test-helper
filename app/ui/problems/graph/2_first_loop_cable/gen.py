LARGE = 2


def valid(cables):
    def name_ok(name):
        return 1 <= len(name) <= 8 and all("a" <= ch <= "z" for ch in name)

    return 1 <= len(cables) <= 100_000 and all(x != y and name_ok(x) and name_ok(y) for x, y in cables)


def names(rng, count, length):
    """서로 다른 이름 count개(알파벳 소문자 length글자)."""
    seen = set()
    out = []
    while len(out) < count:
        name = rng.word(length)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def random_cables(rng, pool, count):
    return [rng.sample(pool, 2) for _ in range(count)]


def small(rng):
    chain = names(rng, 30, 3)
    tree = names(rng, 21, 2)
    cases = [
        [[["a", "b"]]],
        [[["a", "b"], ["b", "a"]]],
        [[["a", "b"], ["c", "d"], ["e", "f"]]],  # 서로 떨어진 케이블만: 이름이 케이블 수의 두 배
        [[["a", "b"], ["c", "d"], ["b", "c"], ["a", "d"]]],  # 바로 위 부모끼리 비교하면 놓친다
        [[["a", "b"], ["c", "d"], ["a", "c"], ["b", "x"], ["x", "d"]]],  # 앞에서 나온 이름끼리 이어도 고리가 아닐 때가 있다
        [[["p", "q"], ["r", "s"], ["q", "r"], ["s", "p"], ["p", "r"]]],
        [[["c", "a"], ["c", "b"], ["c", "d"], ["a", "d"]]],
        [[["zzzzzzzz", "a"], ["a", "zzzzzzzy"], ["zzzzzzzy", "zzzzzzzz"]]],
        [[[chain[i], chain[i + 1]] for i in range(29)] + [[chain[29], chain[0]]]],  # 맨 끝에서 고리
        [[[tree[i], tree[i + 1]] for i in range(0, 20, 2)] + [[tree[i], tree[i + 2]] for i in range(0, 19, 2)]],  # 짝끼리 먼저 잇고 나중에 짝들을 이어 고리가 없다
        [[["mx", "my"], ["ma", "mb"], ["mc", "md"], ["mb", "mc"], ["my", "ma"], ["md", "mx"], ["ma", "mx"]]],
    ]
    pool = ["ant", "bee", "cat", "dog", "eel", "fox", "gnu", "hen"]
    for _ in range(6):
        cases.append([random_cables(rng, pool, rng.randint(4, 12))])
    big = names(rng, 40, 4)
    cases.append([random_cables(rng, big, 60)])
    return cases


def random_small(rng):
    return [random_cables(rng, ["a", "b", "c", "d", "e", "f"], rng.randint(1, 8))]


def large(rng, index):
    leaves = names(rng, 100_000, 5)
    if index == 0:  # [hub, 새 장비]를 이어 가다 마지막에 고리: x쪽에서 탐색하거나 x쪽 대표를 y쪽 아래에 두면 매번 길어진다
        cables = [["hub", leaf] for leaf in leaves[:99_999]]
        cables.append([leaves[5], leaves[77_777]])
        return [cables]
    return [[[leaf, "hub"] for leaf in leaves]]  # 반대 방향, 고리가 없다
