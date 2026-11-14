LARGE = 2


def patients_for(rng, count, spread, longest):
    """도착 시각 0 ~ spread, 진료 시간 1 ~ longest, 위급도 1 ~ 5인 동물 count마리. 정렬하지 않는다."""
    return [[rng.randint(0, spread), rng.randint(1, longest), rng.randint(1, 5)] for _ in range(count)]


def valid(patients):
    return 1 <= len(patients) <= 100_000 and all(
        len(p) == 3 and 0 <= p[0] <= 5_000_000 and 1 <= p[1] <= 500 and 1 <= p[2] <= 5 for p in patients)


def small(rng):
    cases = [
        [[[0, 1, 1]]],
        [[[5000000, 500, 5]]],
        [[[3, 2, 1], [3, 2, 5]]],                        # 같은 시각에 오면 위급도가 큰 것 먼저
        [[[0, 4, 1], [4, 1, 1], [4, 1, 5]]],             # 끝난 바로 그 시각에 온 동물도 후보
        [[[0, 2, 3], [10, 3, 2], [10, 1, 4], [10, 2, 4]]],  # 쉬다가 건너뛴 시각에 셋이 함께 온다
        [[[1, 4, 2], [5, 3, 2], [0, 9, 1]]],             # 위급도가 같으면 진료 시간이 짧은 것(늦게 왔고 번호가 큰 쪽)
        [[[6, 3, 2], [1, 3, 2], [0, 9, 1]]],             # 위급도와 진료 시간이 같으면 번호가 작은 것(늦게 온 쪽)
        [[[0, 10, 1], [1, 1, 1], [2, 1, 2], [3, 1, 3], [4, 1, 4], [5, 1, 5]]],
        [[[0, 500, 1]] + [[1, 500, 5]] * 4],             # 덜 위급한 동물이 오래 기다린다
        [[[i * 10, 3, 5] for i in range(10)]],           # 아무도 기다리지 않는다
        [[[0, 7, 2], [7, 7, 2], [14, 7, 2], [0, 1, 1]]],
        [[[0, 500, 5]] * 30],                            # 모두 같다: 번호 순
        [[[4999990, 500, 1], [5000000, 500, 3], [4999999, 500, 3]]],
    ]
    while len(cases) < 19:
        case = [patients_for(rng, rng.randint(5, 50), rng.choice([10, 100, 1000]), rng.choice([3, 20, 500]))]
        if case not in cases:
            cases.append(case)
    return cases


def random_small(rng):
    return [patients_for(rng, rng.randint(1, 7), rng.choice([3, 8, 20]), rng.choice([2, 4]))]


def large(rng, index):
    n = 100_000
    if index == 0:  # 모두 처음 1초 안에 몰려온다: 기다리는 동물이 10만 마리에 가깝다
        return [patients_for(rng, n, 1, 500)]
    # 진료 시간과 도착 간격이 비슷해 쉬었다 몰렸다를 되풀이하고, 마지막에 가장 늦은 도착 시각까지 간다
    patients = patients_for(rng, n - 1, 5_000_000, 100)
    patients.append([5_000_000, 500, 1])
    return [patients]
