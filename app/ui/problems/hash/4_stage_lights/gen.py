LARGE = 2


def pick(rng, count, m, zero_rate):
    """조명 m개, 버튼 count번. zero_rate/10의 확률로 모두 끄는 버튼."""
    return [[0 if rng.chance(zero_rate, 10) else rng.randint(1, m) for _ in range(count)], m]


def small(rng):
    cases = [
        [[1], 1],  # 한 번 눌러 켠다: 제자리 토막 없음
        [[0], 1],  # 이미 꺼져 있을 때 모두 끈다: 그 한 번이 제자리 토막
        [[1, 1], 1],  # 켰다 끈다
        [[0, 0, 0], 5],  # 모두 끄기만: 모든 토막이 제자리
        [[20, 20], 20],  # 가장 큰 번호
        [[1, 2, 0], 2],  # 짝수 번 눌리지 않았어도 끝에서 모두 꺼진다
        [[1, 0, 1], 2],  # 모두 끄는 버튼을 사이에 두고 같은 상태
        [[1, 2, 1, 2], 2],
        [[3, 1, 3, 1, 3, 1], 3],
        [[1, 2, 3, 1, 2, 3, 0, 1], 3],
        [[2, 0, 2, 0, 2, 0], 2],
        [[1, 1, 1, 1, 1, 1, 1], 1],  # 두 상태가 번갈아 나온다
    ]
    for _ in range(6):
        cases.append(pick(rng, rng.randint(8, 30), rng.randint(1, 4), rng.randint(0, 3)))
    return cases


def random_small(rng):
    return pick(rng, rng.randint(1, 12), rng.randint(1, 3), rng.randint(0, 3))


def large(rng, index):
    count = 200_000
    if index == 0:  # 조명 20개: 상태가 잘 겹치지 않는다
        return pick(rng, count, 20, 0)
    # 조명 3개, 모두 끄는 버튼이 잦다: 같은 상태가 자주 나와 답이 int를 넘는다
    return pick(rng, count, 3, 2)


def valid(presses, m):
    return 1 <= m <= 20 and 1 <= len(presses) <= 200_000 and all(0 <= button <= m for button in presses)
