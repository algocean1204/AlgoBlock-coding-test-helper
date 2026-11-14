LARGE = 2


def segment_sum(rng, gaps):
    """gaps에서 무작위로 고른 이어진 구간의 합(답이 1 이상이 되게)."""
    a = rng.randint(0, len(gaps) - 1)
    b = rng.randint(a, len(gaps) - 1)
    return sum(gaps[a:b + 1])


def small(rng):
    cases = [
        [[5], 5],  # 가장 작은 입력, 답이 1
        [[5], 3],  # 답이 없다
        [[1, 1, 1, 3], 3],  # 왼쪽을 여러 칸 당겨야 한다
        [[1, 2, 3], 5],  # 넘친 뒤 당겨서 k가 된다
        [[3, 3, 3, 3], 3],  # 모두 같은 값
        [[3, 3, 3, 3], 12],  # 전체 구간이 답
        [[10000] * 100, 1000000],  # 가장 큰 값, 전체 구간
        [[10000] * 100, 1000000000],  # 가장 큰 k, 답이 없다
        [[1] * 50, 10],
        [[4, 1, 1, 1, 1, 4], 4],
        [[2, 9, 9, 9, 2], 2],  # 답이 처음과 끝에 있다
        [[9, 1, 1, 1, 1, 1, 1, 1, 1, 9], 9],
    ]
    for _ in range(6):
        gaps = [rng.randint(1, 5) for _ in range(rng.randint(10, 40))]
        cases.append([gaps, segment_sum(rng, gaps)])
    gaps = [rng.randint(1, 10000) for _ in range(150)]
    cases.append([gaps, segment_sum(rng, gaps)])
    return cases


def random_small(rng):
    gaps = [rng.randint(1, 4) for _ in range(rng.randint(1, 10))]
    return [gaps, rng.randint(1, 12)]


def large(rng, index):
    if index == 0:  # 원소가 작고 k가 커서 구간이 길다: 넘칠 때 멈추는 풀이도 구간 길이만큼 더한다
        gaps = [rng.randint(1, 3) for _ in range(100_000)]
        return [gaps, 100_000]
    gaps = [rng.randint(1, 10000) for _ in range(100_000)]
    return [gaps, sum(gaps[40_000:50_000])]


def valid(gaps, k):
    return 1 <= len(gaps) <= 100_000 and all(1 <= gap <= 10000 for gap in gaps) and 1 <= k <= 1_000_000_000
