LARGE = 2


def total(schedules):
    return sum(times for first, gap, times in schedules)


def small(rng):
    cases = [
        [[[1, 1, 1]], 1],  # 가장 작은 입력
        [[[7, 3, 5]], 5],  # 시설 하나의 마지막 점검
        [[[7, 3, 5]], 2],
        [[[4, 1, 3], [4, 1, 3]], 4],  # 일정이 같은 두 시설
        [[[2, 5, 3], [3, 5, 3]], 6],
        [[[10, 1, 1], [1, 1, 3]], 4],  # 끝난 일정 뒤의 날
        [[[1, 4, 3], [2, 4, 3], [3, 4, 3]], 7],  # 점검이 없는 날(4일, 8일)
        [[[1, 10, 2], [1, 1, 10]], 11],  # 11일: 하루에 두 번
        [[[1, 10, 2], [1, 1, 10]], 12],
        [[[50, 1, 3], [1, 100, 2]], 2],  # 첫 점검이 늦은 시설: 그 전에는 0번
        [[[50, 1, 3], [1, 100, 2]], 5],
        [[[1000000000, 1000000, 3], [999999999, 1, 2]], 3],  # 가장 큰 first
        [[[3, 7, 4], [3, 7, 4], [3, 7, 4]], 12],  # 모두 같은 날
        [[[5, 1000000, 2], [6, 1, 30]], 31],
        [[[9, 2, 6], [1, 3, 4], [20, 1, 1], [8, 8, 2]], 9],
    ]
    for _ in range(5):
        schedules = [[rng.randint(1, 40), rng.randint(1, 6), rng.randint(1, 12)] for _ in range(rng.randint(1, 8))]
        cases.append([schedules, rng.randint(1, total(schedules))])
    return cases


def medium(rng):  # 날이 int를 넘는다: 모든 점검일을 만드는 풀이로는 못 돌린다
    return [
        [[[1000000000, 1000000, 1000000]], 1000000],  # 마지막 점검일 1,000,999,000,000
        [[[1000000000, 1000000, 1000000], [1, 1000000, 1000000]], 1999999],
        [[[2000, 1000000, 1000000], [1000, 999999, 1000000], [3000, 1000000, 999999]], 2999998],
    ]


def valid(schedules, k):
    if not (1 <= len(schedules) <= 40_000):
        return False
    for row in schedules:
        if len(row) != 3:
            return False
        first, gap, times = row
        if not (1 <= first <= 10**9 and 1 <= gap <= 10**6 and 1 <= times <= 10**6):
            return False
    return 1 <= k <= total(schedules)


def random_small(rng):
    schedules = [[rng.randint(1, 12), rng.randint(1, 4), rng.randint(1, 5)] for _ in range(rng.randint(1, 4))]
    return [schedules, rng.randint(1, total(schedules))]


def large(rng, index):
    if index == 0:  # 점검이 400억 번 가까이, k가 끝 쪽: 점검 수와 날이 int를 한참 넘는다
        schedules = [[rng.randint(1, 10**9), rng.randint(1, 10**6), rng.randint(900_000, 10**6)] for _ in range(40_000)]
        whole = total(schedules)
        return [schedules, rng.randint(whole - whole // 10, whole)]
    # 간격이 좁아 같은 날이 많다
    schedules = [[rng.randint(1, 1000), rng.randint(1, 50), rng.randint(1, 10**6)] for _ in range(40_000)]
    return [schedules, rng.randint(total(schedules) // 3, total(schedules))]
