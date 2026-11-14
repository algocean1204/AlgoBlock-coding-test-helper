LARGE = 2


def small(rng):
    cases = [
        [[7], 1],
        [[500000000, 1], 2],                       # 가장 큰 차이
        [[500000000, 1], 1],                       # 판자 하나만 고르면 비용이 없다
        [[1, 7], 1],                                # 높이가 늘어나는 w = 1
        [[5, 5, 5, 5], 3],                          # 모두 같은 높이
        [[1, 2, 3, 4, 5, 6, 7], 4],                 # 점점 높아진다
        [[1, 2, 3, 3], 3],                          # 빼고 난 뒤 개수를 다시 맞춰야 한다
        [[9, 1, 9, 1, 9, 1], 3],
        [[3, 3, 3, 50, 1, 1, 2], 3],
        [[5, 1, 9, 2], 3],                          # 방금 빠진 판자를 창 안으로 보면 두 번째 견적이 틀린다
        [[10, 18, 23, 11, 20, 10], 3],              # 방금 빠진 판자가 작은 쪽 꼭대기에 남는다
        [[20, 27, 22, 16, 17, 1], 3],
        [[2, 2, 2, 4, 4, 12, 1, 3, 2, 1, 4, 6], 2],  # 같은 높이가 두 힙에 나뉜다
        [[6, 6, 6, 1, 6, 1, 6, 1, 1], 4],
    ]
    for _ in range(5):
        n = rng.randint(8, 40)
        cases.append([[rng.randint(1, 20) for _ in range(n)], rng.randint(2, n)])
    cases.append([[rng.randint(1, 500000000) for _ in range(120)], 40])
    return cases


def random_small(rng):
    n = rng.randint(1, 10)
    top = rng.choice([3, 6, 9])
    return [[rng.randint(1, top) for _ in range(n)], rng.randint(1, n)]


def valid(heights, w):
    return 1 <= len(heights) <= 100_000 and all(1 <= height <= 500_000_000 for height in heights) and 1 <= w <= len(heights)


def large(rng, index):
    n = 100_000
    # 출력(구간 수 × 숫자 길이)이 1,000,000바이트 안에 들도록 w를 크게 둔다. 지우기를 바로 하는 풀이는 (n - w) × w에 비례해 느리다
    if index == 0:
        return [[rng.randint(1, 500_000_000) for _ in range(n)], 60_000]
    # 점점 높아진다: 빠지는 판자가 늘 작은 쪽 힙 깊숙이 있어 지울 표시만 한 판자가 많이 쌓인다
    return [[i * 4_500 + rng.randint(1, 50_000) for i in range(n)], 80_000]
