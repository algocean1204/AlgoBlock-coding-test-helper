LARGE = 2
TOP = 100_000_000


def logs_for(rng, count, high, step=1):
    out = []
    for _ in range(count):
        login = rng.randint(0, high // step - 1) * step
        out.append([login, rng.randint(login // step + 1, high // step) * step])
    return out


def small(rng):
    cases = [
        [[[0, 1]]],  # 가장 작은 입력
        [[[0, TOP]]],  # 가장 긴 접속 하나
        [[[5, 6], [5, 6], [5, 6]]],  # 모두 같은 기록
        [[[0, 5], [5, 10], [10, 15]]],  # 끊는 초에 다음 사용자가 접속한다: 접속을 먼저 처리하면 틀린다
        [[[0, 10], [10, 20], [5, 15]]],
        [[[0, 100], [10, 20], [30, 40]]],  # 긴 접속 안에 짧은 접속 둘: 최댓값인 때가 떨어져 있다
        [[[0, 2], [5, 7], [10, 12]]],  # 겹치지 않는다
        [[[3, 4], [3, 8], [3, 6]]],  # 같은 초에 함께 접속
        [[[0, TOP], [TOP - 1, TOP]]],  # 가장 큰 시각
        [[[0, 50], [40, 41]]],  # 오래 1명이다가 잠깐 2명: 최댓값이 바뀌면 시간을 새로 센다
        [[[1, 3], [3, 5], [3, 5], [1, 3]]],  # 두 명이 끊는 초에 두 명이 접속
        [[[20, 30], [0, 10], [10, 20]]],  # 정렬되지 않은 입력
    ]
    cases.append([logs_for(rng, 100, 100, 10)])  # 10초 단위: 같은 초의 사건이 많다
    for _ in range(2):
        cases.append([logs_for(rng, rng.randint(10, 30), 30)])
    for _ in range(2):
        cases.append([logs_for(rng, rng.randint(20, 60), TOP)])  # 큰 시각
    return cases


def random_small(rng):
    return [logs_for(rng, rng.randint(1, 6), 12)]


def large(rng, index):
    n = 100_000
    if index == 0:  # 길게 겹치는 접속: 한 사용자가 사건 시각 사이 칸을 절반 넘게 걸친다
        out = []
        for _ in range(n):
            login = rng.randint(0, TOP // 2)
            out.append([login, login + rng.randint(TOP * 3 // 10, TOP // 2)])
        return [out]
    return [logs_for(rng, n, TOP, 1000)]  # 1000초 단위: 같은 초에 끊고 접속하는 일이 아주 많다
