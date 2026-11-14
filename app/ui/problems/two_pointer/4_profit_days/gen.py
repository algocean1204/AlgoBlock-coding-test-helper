LARGE = 3


def segment_sum(rng, profits):
    """profits에서 무작위로 고른 이어진 기간의 합(답이 1 이상이 되게)."""
    a = rng.randint(0, len(profits) - 1)
    b = rng.randint(a, len(profits) - 1)
    return sum(profits[a:b + 1])


def small(rng):
    cases = [
        [[5], 5],  # 가장 작은 입력, 답이 1
        [[5], -5],  # 답이 없다
        [[-10000], -10000],  # 가장 작은 값
        [[0], 0],
        [[1, -1, 1, -1], 0],  # 같은 누적 합이 여러 번 나온다
        [[0, 0, 0, 0, 0], 0],  # 모두 같은 값, target이 0
        [[10000] * 100, 1000000],  # 가장 큰 값, 전체 기간
        [[-10000] * 100, -1000000],
        [[10000] * 100, -1000000000],  # 가장 작은 target, 답이 없다
        [[1, 2, 3], 7],  # 답이 없다
        [[4, -4, 4, -4, 4], 4],
        [[-1, -2, -3], -3],  # 모두 음수
        [[5, -7, 2, 5], 5],  # 합이 넘친 뒤 음수로 다시 맞춰진다
    ]
    for _ in range(6):
        profits = [rng.randint(-5, 5) for _ in range(rng.randint(10, 40))]
        cases.append([profits, segment_sum(rng, profits)])
    profits = [rng.randint(-10000, 10000) for _ in range(150)]
    cases.append([profits, segment_sum(rng, profits)])
    return cases


def random_small(rng):
    profits = [rng.randint(-3, 3) for _ in range(rng.randint(1, 10))]
    if rng.chance(1, 2):  # 절반은 실제로 있는 기간의 합: 답이 0으로 쏠리지 않게
        return [profits, segment_sum(rng, profits)]
    return [profits, rng.randint(-4, 4)]


def large(rng, index):
    if index == 0:
        profits = [rng.randint(-10000, 10000) for _ in range(100_000)]
        return [profits, sum(profits[30_000:70_000])]
    if index == 1:  # 같은 누적 합이 아주 많이 나온다
        return [[rng.randint(-1, 1) for _ in range(100_000)], 0]
    return [[0] * 100_000, 0]  # 모든 기간이 답: 약 50억 개로 int를 넘는다


def valid(profits, target):
    return 1 <= len(profits) <= 100_000 and all(-10000 <= profit <= 10000 for profit in profits) and -1_000_000_000 <= target <= 1_000_000_000
