LARGE = 2


def pairs(rng, n, count):
    found = []
    while len(found) < count:
        a, b = sorted(rng.sample(list(range(n)), 2))
        if [a, b] not in found:
            found.append([a, b])
    return found


def table(rng, members, roles, blank, high):
    """단원 members명이 배역 roles개의 오디션을 본 기록. blank/10의 확률로 그 배역의 오디션을 보지 않는다(적어도 하나는 남긴다)."""
    found = [[member, role, rng.randint(1, high)] for member in range(members) for role in range(roles) if not rng.chance(blank, 10)]
    if not found:
        found = [[rng.randint(0, members - 1), rng.randint(0, roles - 1), rng.randint(1, high)]]
    return rng.shuffle(found)


def full(members, roles, score):
    return [[member, role, score(member, role)] for member in range(members) for role in range(roles)]


def small(rng):
    # 정확성 케이스는 단원 8명, 배역 6개까지(정의 그대로 풀이와 느린 풀이도 답은 맞게 끝나야 한다). 14명·9개는 medium과 효율성 케이스가 쓴다.
    cases = [
        [2, 1, [[0, 0, 7], [1, 0, 3]], [[0, 1]]],  # 가장 작은 입력: 한 배역
        [2, 1, [[0, 0, 7]], [[0, 1]]],
        [2, 2, [[0, 0, 1], [0, 1, 1], [1, 0, 1], [1, 1, 1]], [[0, 1]]],  # 둘 다 필요한데 함께 설 수 없다
        [3, 2, [[0, 0, 5], [0, 1, 5], [1, 0, 1], [1, 1, 1], [2, 0, 1], [2, 1, 1]], [[1, 2]]],  # 한 사람에게 두 배역을 맡기면 틀린다
        [3, 1, [[0, 0, 500], [1, 0, 500], [2, 0, 500]], [[0, 1], [0, 2], [1, 2]]],  # 혼자면 부딪칠 사람이 없다
        [3, 2, [[0, 0, 3], [1, 1, 3], [2, 0, 9], [2, 1, 9]], [[0, 2], [1, 2]]],  # 가장 높은 사람을 쓰면 나머지를 못 채운다
        [3, 2, [[0, 0, 1], [0, 1, 9], [1, 0, 9], [1, 1, 1], [2, 0, 5], [2, 1, 5]], [[0, 1]]],  # 번호가 작은 사람을 나중에 정해야 부딪친다
        [3, 2, [[0, 1, 6], [1, 0, 6], [1, 1, 4], [2, 0, 5]], [[1, 2]]],
        [4, 3, full(4, 3, lambda m, r: [[10, 1, 1], [9, 9, 1], [1, 9, 9], [1, 1, 10]][m][r]), [[0, 3]]],  # 앞에서 욕심내면 손해
        [4, 3, [[0, 0, 2], [1, 1, 2], [2, 2, 2], [3, 0, 2], [3, 1, 2], [3, 2, 2]], [[0, 3], [1, 3]]],
        [8, 4, full(8, 4, lambda m, r: 500), [[0, 1], [2, 3], [4, 5], [6, 7]]],  # 가장 큰 점수: 짝마다 한 명씩만 써서 2,000
        [4, 3, full(3, 3, lambda m, r: 5 - r) + [[3, 0, 1]], [[0, 1], [1, 2], [0, 2]]],  # 셋 가운데 한 명만 쓸 수 있다: 채울 수 없다
        [5, 4, [[0, 0, 1], [1, 1, 1], [2, 2, 1], [3, 3, 1], [4, 0, 5], [4, 1, 5], [4, 2, 5], [4, 3, 5]], [[0, 4]]],
        [4, 2, [[0, 0, 4], [1, 0, 3]], [[2, 3]]],  # 1번 배역의 오디션을 본 단원이 없다
    ]
    while len(cases) < 19:
        members = rng.randint(3, 8)
        roles = rng.randint(1, min(6, members))
        cases.append([members, roles, table(rng, members, roles, rng.randint(1, 5), rng.choice([5, 500])),
                      pairs(rng, members, rng.randint(1, min(6, members * (members - 1) // 2)))])
    return cases


def medium(rng):
    # 단원 14명, 배역 9개. 둘 다 손으로 따질 수 있다.
    return [
        [14, 9, full(14, 9, lambda m, r: 10), [[0, 1]]],  # 누구든 10점: 9명을 고를 수 있으므로 90
        [14, 9, full(14, 9, lambda m, r: m + 1), [[12, 13]]],  # 높은 사람부터 쓰되 12·13번은 한 명만: 14 + 12 + 11 + … + 5 = 82
    ]


def valid(members, roles, auditions, rivals):
    if not (1 <= members <= 14 and 1 <= roles <= 9 and 1 <= len(auditions) <= members * roles):
        return False
    if any(len(a) != 3 or not (0 <= a[0] < members and 0 <= a[1] < roles and 1 <= a[2] <= 500) for a in auditions):
        return False
    if len({(a[0], a[1]) for a in auditions}) != len(auditions):
        return False
    return (1 <= len(rivals) <= 25 and all(len(p) == 2 and 0 <= p[0] < p[1] < members for p in rivals)
            and len({tuple(p) for p in rivals}) == len(rivals))


def random_small(rng):
    members = rng.randint(2, 6)
    roles = rng.randint(1, min(4, members))
    return [members, roles, table(rng, members, roles, rng.randint(1, 4), 6), pairs(rng, members, rng.randint(1, min(3, members * (members - 1) // 2)))]


def large(rng, index):
    if index == 0:  # 누구나 어느 배역이든 오디션을 보았고 부딪치는 짝이 적다: 배정은 7억 가지가 넘는다
        return [14, 9, table(rng, 14, 9, 0, 500), pairs(rng, 14, 2)]
    # 오디션을 보지 않은 배역과 부딪치는 짝이 섞인다
    return [14, 9, table(rng, 14, 9, 1, 500), pairs(rng, 14, 6)]
