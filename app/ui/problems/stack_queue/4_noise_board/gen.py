LARGE = 2


def make_logs(rng, count, start, max_gap, max_level):
    logs, time = [], start
    for _ in range(count):
        logs.append([time, rng.randint(1, max_level)])
        time += rng.randint(1, max_gap)
    return logs


def valid(logs, window):
    times = [log[0] for log in logs]
    return (1 <= len(logs) <= 100_000 and 1 <= window <= 10_000_000
            and all(len(log) == 2 and 0 <= log[0] <= 10_000_000 and 1 <= log[1] <= 100_000 for log in logs)
            and all(a < b for a, b in zip(times, times[1:])))


def small(rng):
    cases = [
        [[[0, 1]], 1],
        [[[0, 5], [1, 3]], 1],                                   # 창 왼쪽 끝은 들어가지 않는다
        [[[0, 9], [1, 8], [100, 1]], 5],                         # 한꺼번에 둘이 창을 벗어난다
        [[[0, 1], [1, 2], [2, 3], [3, 4]], 2],                   # 커지기만 한다
        [[[0, 4], [3, 4], [6, 4], [9, 4]], 4],                   # 모두 같은 값
        [[[0, 100000], [10000000, 1]], 10000000],                # 가장 큰 시각과 창: 0초는 빠진다
        [[[0, 100000], [9999999, 1]], 10000000],                 # 0초가 아직 들어 있다
        [[[0, 10], [1, 9], [2, 8], [3, 7], [4, 6]], 3],          # 줄어들기만 한다
        [[[2, 3], [4, 7], [5, 2], [6, 7], [9, 1], [11, 6]], 4],  # 같은 값이 다시 나온다
    ]
    for max_gap, max_level, window in [(3, 20, 6), (5, 100000, 12), (1, 5, 3), (10, 50, 1), (4, 1000, 30)]:
        cases.append([make_logs(rng, rng.randint(40, 100), rng.randint(0, 5), max_gap, max_level), window])
    while len(cases) < 18:
        case = [make_logs(rng, rng.randint(5, 20), rng.randint(0, 3), rng.randint(1, 4), rng.choice([3, 9])), rng.randint(1, 8)]
        if case not in cases:
            cases.append(case)
    return cases


def random_small(rng):
    return [make_logs(rng, rng.randint(1, 10), rng.randint(0, 2), rng.randint(1, 3), rng.choice([2, 5, 9])), rng.randint(1, 8)]


def large(rng, index):
    n = 100_000
    if index == 0:  # 창이 모든 기록을 덮는다: 기록마다 창 안을 훑으면 n × n / 2번
        return [make_logs(rng, n, rng.randint(0, 10), 100, 100_000), 10_000_000]
    # 소음이 줄어들기만 하고 창에 기록 5만 개: 가장 큰 값이 매번 창을 벗어난다
    return [[[time, 100_000 - time] for time in range(n)], 50_000]
