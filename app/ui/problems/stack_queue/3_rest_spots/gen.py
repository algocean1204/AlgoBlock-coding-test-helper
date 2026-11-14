LARGE = 2


def valid(heights):
    return 1 <= len(heights) <= 150_000 and all(1 <= height <= 1_000_000_000 for height in heights)


def small(rng):
    cases = [
        [[1]],
        [[1000000000, 1000000000]],
        [[2, 1]],
        [[1, 2]],
        [[1, 2, 3, 4, 5, 6]],            # 계속 오른다: 아무도 쉬지 못한다
        [[6, 5, 4, 3, 2, 1]],            # 계속 내린다: 모두 바로 옆에서 쉰다
        [[3, 3, 3, 3, 3]],               # 같은 높이에서도 쉰다
        [[2, 2, 1, 2, 2]],
        [[3, 1, 3, 1, 3]],
        [[5, 9, 9, 5, 4, 9, 1]],
        [[7, 8, 9, 6, 7, 8, 5]],         # 오르막 뒤 한 지점이 여럿을 한꺼번에 받는다
        [[4, 6, 5, 7, 3, 8, 8]],         # 내리막(6 → 5)이 있어도 출발 높이보다 높으면 지나간다
        [[1000000000, 1, 1000000000]],
    ]
    cases.append([[rng.randint(1, 1_000_000_000) for _ in range(150)]])
    cases.append([sorted(rng.randint(2, 50) for _ in range(150)) + [1]])  # 오르다가 맨 끝에서만 떨어진다
    while len(cases) < 19:
        case = [[rng.randint(1, rng.choice([3, 6, 20])) for _ in range(rng.randint(5, 40))]]
        if case not in cases:
            cases.append(case)
    return cases


def random_small(rng):
    return [[rng.randint(1, rng.choice([2, 3, 5])) for _ in range(rng.randint(1, 10))]]


def large(rng, index):
    n = 150_000
    if index == 0:  # 계속 높아지다 맨 끝에서 가장 낮아진다: 모든 등산객이 끝까지 걷는다
        return [sorted(rng.randint(2, 1_000_000_000) for _ in range(n - 1)) + [1]]
    # 산 모양(오르막은 서로 다른 높이): 오르막의 등산객은 반대편 내리막까지 걸어가야 쉰다
    up = list(range(1, n // 2 + 1))
    return [up + up[::-1]]
