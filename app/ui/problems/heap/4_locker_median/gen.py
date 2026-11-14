LARGE = 2


def small(rng):
    cases = [
        [[0]],
        [[1000000]],
        [[5, 5, 5, 5]],                          # 모두 같은 위치
        [[0, 1000000]],
        [[1, 2, 3, 4, 5, 6]],                    # 점점 오른쪽
        [[6, 5, 4, 3, 2, 1]],                    # 점점 왼쪽
        [[0, 1000000, 0, 1000000, 0]],           # 양 끝을 오간다
        [[10, 0, 10, 0, 10, 0, 10]],
        [[4, 1, 7, 1, 9, 2, 2]],
        [[0, 0, 0, 100, 100, 100, 100]],         # 가운데 값이 한쪽에서 다른 쪽으로 넘어간다
    ]
    for _ in range(7):
        cases.append([[rng.randint(0, 20) for _ in range(rng.randint(5, 30))]])
    cases.append([[rng.randint(0, 1000000) for _ in range(100)]])
    return cases



def medium(rng):
    # 답이 int(약 21억)를 넘는다. 손으로 따질 수 있는 모양을 섞는다
    return [
        [[0, 1000000] * 100],                              # d일째 거리 합은 (d // 2) × 1,000,000, 모두 10,000,000,000
        [[i * 5000 for i in range(200)]],                  # 점점 오른쪽으로 고르게
        [[1000000] * 100 + [0] * 100],                     # 한쪽에 몰렸다가 다른 쪽으로
        [[rng.randint(0, 1000000) for _ in range(180)]],
    ]


def random_small(rng):
    return [[rng.randint(0, 8) for _ in range(rng.randint(1, 9))]]


def large(rng, index):
    n = 100_000
    if index == 0:
        return [[rng.randint(0, 1_000_000) for _ in range(n)]]
    # 왼쪽 끝과 오른쪽 끝을 오가며 조금씩 가운데로 모인다: 두 힙 사이로 값이 자주 옮겨 간다
    return [[i * 5 if i % 2 == 0 else 1_000_000 - i * 5 for i in range(n)]]


def valid(houses):
    return 1 <= len(houses) <= 100_000 and all(0 <= house <= 1_000_000 for house in houses)
