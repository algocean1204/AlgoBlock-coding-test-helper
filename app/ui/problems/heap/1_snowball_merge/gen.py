LARGE = 2


def small(rng):
    cases = [
        [[1]],
        [[10000]],
        [[1, 1]],
        [[10000, 1]],
        [[1, 2, 3, 4, 5]],          # 이미 정렬됨
        [[5, 4, 3, 2, 1]],          # 거꾸로 정렬됨
        [[3, 3, 3, 3, 3, 3, 3]],    # 모두 같은 무게
        [[1, 1, 1, 1, 100]],        # 아주 무거운 것 하나는 맨 마지막에 합쳐진다
        [[10000, 10000, 10000]],
        [[6, 1, 1, 6]],
        [[2, 9, 2, 9, 2, 9]],
    ]
    for _ in range(6):
        cases.append([[rng.randint(1, 50) for _ in range(rng.randint(3, 30))]])
    cases.append([[rng.randint(1, 10000) for _ in range(150)]])
    return cases


def random_small(rng):
    return [[rng.randint(1, 6) for _ in range(rng.randint(1, 9))]]


def large(rng, index):
    if index == 0:
        return [[rng.randint(1, 10000) for _ in range(200_000)]]
    return [[10000] * 200_000]  # 모두 가장 무거운 값: 힘의 합이 32비트 정수를 넘는다


def valid(snowballs):
    return 1 <= len(snowballs) <= 200_000 and all(1 <= weight <= 10000 for weight in snowballs)
