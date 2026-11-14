LARGE = 0

EXAMPLES = [[10, 7, 2, 4], [12, 8, 2, 5], [5, 4, 3, 4]]


def small(rng):
    cases = [
        [1, 1, 1, 1],                        # 가장 작은 입력
        [1_000_000, 1_000_000, 1, 100_000],  # 가장 큰 값: 남김없이 담기는 크기가 여럿이다
        [1, 1_000_000, 50_000, 100_000],     # 사과는 늘 1개 남는다
        [3, 2, 4, 6],                        # 모든 size가 과일보다 커서 모두 남는다: 가장 큰 size, 상자 0개
        [7, 7, 4, 4],                        # 남는 과일을 합치면 한 상자가 더 찬다: 상자 수를 합쳐 나누면 틀린다
        [8, 7, 3, 5],                        # 합치면 3과 5가 남김없이 담긴다
        [12, 12, 5, 6],                      # 답이 high다
        [6, 6, 1, 3],                        # 모든 size에서 남지 않는다: 가장 큰 3
        [999_999, 1, 7, 7],                  # low와 high가 같다
        [100, 99, 1, 100_000],
        [720_720, 360_360, 2, 99_991],
    ]
    while len(cases) < 18:
        low = rng.randint(1, 60)
        args = [rng.randint(1, 5_000), rng.randint(1, 5_000), low, rng.randint(low, 120)]
        if args not in cases and args not in EXAMPLES:
            cases.append(args)
    return cases


def valid(apples, pears, low, high):
    return 1 <= apples <= 1_000_000 and 1 <= pears <= 1_000_000 and 1 <= low <= high <= 100_000


def random_small(rng):
    low = rng.randint(1, 12)
    return [rng.randint(1, 40), rng.randint(1, 40), low, rng.randint(low, 15)]
