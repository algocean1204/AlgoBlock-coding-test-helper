LARGE = 1


def times_for(rng, count, spread):
    """줄어들지 않는 도착 시각 count개. spread가 작을수록 한꺼번에 몰려온다."""
    times = sorted(rng.randint(0, spread) for _ in range(count))
    return times


def valid(arrive, ride, gap, cap):
    return (1 <= len(arrive) <= 1_000 and all(0 <= t <= 100_000 for t in arrive)
            and all(arrive[i] <= arrive[i + 1] for i in range(len(arrive) - 1))
            and 1 <= ride <= 1_000 and 1 <= gap <= 100 and 1 <= cap <= 100)


def small(rng):
    cases = [
        [[0], 1, 1, 1],
        [[100000], 1000, 100, 100],
        [[0, 0], 1, 1, 1],                 # 벗어나는 바로 그 초에 다음 사람이 출발한다
        [[0, 0, 0], 3, 1, 1],
        [[0, 0, 0, 0], 2, 3, 1],           # gap이 ride보다 길다
        [[5, 5, 5, 5, 5], 1, 1, 100],      # 자리는 넉넉하고 gap만 막는다
        [[0, 1, 2, 3, 4, 5], 4, 1, 2],     # 자리가 막는다
        [[0, 3, 6, 9], 3, 3, 1],           # 도착하자마자 차례로 출발: 아무도 기다리지 않는다
        [[0, 2, 2, 50, 50, 51], 10, 2, 2], # 쉬었다가 다시 몰려온다
        [[0, 0, 1, 1, 2, 2, 3, 3], 5, 1, 3],
        [[0] * 30, 1000, 1, 1],            # 한 명씩만 들어간다: 기다림이 길다
        [[0] * 40, 7, 100, 100],           # gap만으로 기다린다
    ]
    while len(cases) < 18:
        count = rng.randint(5, 60)
        case = [times_for(rng, count, rng.choice([5, 50, 500])), rng.randint(1, 40), rng.randint(1, 6), rng.randint(1, 6)]
        if case not in cases:
            cases.append(case)
    return cases


def random_small(rng):
    count = rng.randint(1, 7)
    return [times_for(rng, count, rng.choice([2, 6, 15])), rng.randint(1, 6), rng.randint(1, 3), rng.randint(1, 3)]


def large(rng, index):
    # 모두 0초에 와서 한 명씩만 들어간다: 마지막 사람이 내려오는 데 1,000 × 1,000초가 걸린다
    return [[0] * 1_000, 1_000, rng.randint(1, 100), 1]
