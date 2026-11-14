LARGE = 2
TOP = 1_000_000


def scores(rng, count, high):
    return [[rng.randint(0, high) for _ in range(count)], [rng.randint(0, high) for _ in range(count)]]


def small(rng):
    cases = [
        [[0], [0]],  # 가장 작은 입력
        [[TOP], [TOP]],  # 가장 큰 점수
        [[5, 5], [5, 5]],  # 두 점수가 모두 같은 두 사람: 둘 다 오른다
        [[3, 3], [5, 1]],  # 맛 점수가 같은 무리에서 모양 점수가 높은 사람이 먼저 나온다
        [[5, 4, 3], [9, 1, 5]],  # 바로 앞 사람이 아니라 더 앞의 사람이 떨어뜨린다
        [[1, 2], [5, 5]],  # 모양 점수가 같으면 지지 않는다
        [[1, 2], [9, 1]],  # 맛 점수가 낮은 사람의 모양 점수가 높아도 상관없다
        [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]],  # 서로 엇갈려 아무도 떨어지지 않는다
        [[5, 4, 3, 2, 1], [50, 40, 30, 20, 10]],  # 이미 큰 순서: 한 명만 오른다
        [[10, 10, 10, 10], [1, 2, 3, 4]],  # 모두 맛 점수가 같다
        [[2, 2, 1, 1], [1, 3, 2, 4]],
        [[0, TOP, 0, TOP], [TOP, 0, 0, TOP]],  # 두 점수가 모두 가장 높은 사람이 있어도, 한 점수가 같은 사람은 남는다
    ]
    cases.append(scores(rng, 30, 3))  # 동점투성이
    for _ in range(2):
        cases.append(scores(rng, rng.randint(20, 60), 10))
    cases.append(scores(rng, 90, TOP))  # 큰 점수
    return cases


def random_small(rng):
    n = rng.randint(1, 8)
    return scores(rng, n, 4)


def large(rng, index):
    n = 100_000
    if index == 0:  # 맛 점수가 높을수록 모양 점수가 낮다: 아무도 떨어지지 않아 모든 쌍을 끝까지 본다
        tastes = sorted(rng.distinct(0, TOP, n))
        looks = sorted(rng.distinct(0, TOP, n), reverse=True)
        order = rng.shuffle(list(range(n)))
        return [[tastes[i] for i in order], [looks[i] for i in order]]
    return [[rng.randint(0, 1000) for _ in range(n)], [rng.randint(0, TOP) for _ in range(n)]]  # 맛 점수 동점이 아주 많다
