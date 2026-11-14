LARGE = 2


def pick(rng, count, close, longest, promise_rate):
    """close까지의 시간에서 머무는 시간 1~longest인 자원봉사자 count명. promise_rate/4의 확률로 약속한 사람."""
    helpers = []
    for _ in range(count):
        arrive = rng.randint(0, close - 1)
        leave = min(close, arrive + rng.randint(1, longest))
        helpers.append([arrive, leave, 1 if rng.chance(promise_rate, 4) else 0])
    return helpers


def small(rng):
    cases = [
        [[[0, 10, 0]], 10, 0],  # 한 명이 처음부터 끝까지
        [[[0, 10, 1]], 10, 0],  # 약속한 사람만으로 된다
        [[[3, 5, 0]], 10, 10],  # gap이 close와 같다: 아무도 없어도 된다
        [[[2, 9, 0]], 10, 2],  # 처음 2분, 끝 1분이 빈다
        [[[3, 9, 0]], 10, 2],  # 처음 3분이 빈다: 안 된다
        [[[0, 4, 0], [4, 10, 0]], 10, 0],  # 떠나는 시각에 온다: 빈틈 없음
        [[[0, 4, 0], [5, 10, 0]], 10, 0],  # 1분이 빈다
        [[[0, 4, 0], [5, 10, 0]], 10, 1],  # 1분까지는 괜찮다
        [[[0, 8, 0], [2, 3, 1], [7, 12, 0]], 12, 0],  # 약속한 사람이 이미 지킨 범위 안에서 떠난다
        [[[0, 8, 0], [5, 10, 0]], 10, 2],  # 끝의 2분은 비워도 된다
        [[[0, 5, 1], [5, 10, 1], [0, 10, 0]], 10, 0],  # 약속한 사람끼리 이어진다
        [[[0, 4, 0], [1, 8, 0], [3, 9, 0], [9, 12, 0]], 12, 0],  # 가장 오래 머무는 사람이 가장 늦게 떠나지 않는다
        [[[0, 2, 1], [1, 4, 0], [3, 6, 1], [5, 8, 1], [7, 10, 0]], 10, 0],  # 약속한 사람이 이어져 끝이 두 번 늘어난다
        [[[0, 1000000000, 0]], 1000000000, 0],  # 가장 큰 값
    ]
    for _ in range(6):
        close = rng.randint(10, 40)
        cases.append([pick(rng, rng.randint(4, 10), close, rng.randint(3, 15), rng.randint(0, 2)), close, rng.randint(0, 3)])
    return cases


def random_small(rng):
    close = rng.randint(5, 16)
    return [pick(rng, rng.randint(2, 9), close, rng.randint(close // 3 + 1, close), rng.randint(0, 2)), close, rng.randint(0, 3)]


def large(rng, index):
    close = 1_000_000_000
    helpers = []
    if index == 0:  # 불러야 오는 사람 50,000명이 한 줄로 이어진다: 거의 모두 불러야 한다. 짧게 머무는 사람이 섞인다
        chain, step = 50_000, close // 50_000
        for k in range(chain):
            arrive = max(0, k * step - rng.randint(0, 3000))
            leave = min(close, (k + 1) * step + rng.randint(0, 3000))
            helpers.append([arrive, leave, 0])
        helpers[-1][1] = close
        helpers += pick(rng, 30_000, close, 8000, 1)
        return [rng.shuffle(helpers), close, 500]
    # 약속한 사람과 불러야 오는 사람이 번갈아 지킨다: 약속한 사람 사이마다 한 명씩 불러야 한다
    blocks, size = 20_000, close // 20_000
    for k in range(blocks):
        start = k * size
        helpers.append([start, start + size // 2, 1])
        for _ in range(3):  # 다음 약속까지 이어 줄 후보 셋
            arrive = start + size // 2 - rng.randint(0, 1000)
            leave = min(close, start + size + rng.randint(-1500, 1500))
            helpers.append([arrive, leave, 0])
        helpers[-1][1] = min(close, start + size + rng.randint(0, 1500))  # 셋 가운데 하나는 다음 약속에 닿는다
    return [rng.shuffle(helpers), close, 1000]


def valid(helpers, close, gap):
    return (1 <= len(helpers) <= 80_000 and 1 <= close <= 1_000_000_000 and 0 <= gap <= close
            and all(len(h) == 3 and 0 <= h[0] < h[1] <= close and h[2] in (0, 1) for h in helpers))
