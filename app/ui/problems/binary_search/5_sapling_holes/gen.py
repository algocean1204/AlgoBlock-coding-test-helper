LARGE = 2
TOP = 800_000_000


def valid(trees, holes, count):
    every = list(trees) + list(holes)
    return (1 <= len(trees) <= 50_000 and 1 <= len(holes) <= 100_000 and 1 <= count <= len(holes)
            and all(0 <= x <= TOP for x in every) and len(set(every)) == len(every))


def split(rng, positions, tree_count):
    """서로 다른 위치를 섞어 앞의 tree_count개는 큰 나무, 나머지는 구덩이로 나눈다."""
    positions = rng.shuffle(list(positions))
    return positions[:tree_count], positions[tree_count:]


def small(rng):
    cases = [
        [[0], [1], 1],  # 가장 작은 입력
        [[5], [0, 10], 2],  # 큰 나무 양쪽에 하나씩
        [[0, 100], [50], 1],  # 큰 나무 사이 가운데
        [[0, 3], [100, 200], 1],  # 큰 나무끼리 이미 3: 묘목을 멀리 심어도 답은 3
        [[0, 100], [1, 2, 3, 97, 98, 99], 2],  # 큰 나무 바로 옆 구덩이뿐
        [[10, 30], [2, 14, 19, 25, 41], 3],
        [[40], [0, 10, 20, 30, 50, 60, 70, 80], 8],  # 구덩이를 모두 쓴다
        [[40], [0, 10, 20, 30, 50, 60, 70, 80], 1],  # 하나만: 가장 먼 끝
        [[7], [0, 3, 11, 14], 3],  # 큰 나무 한 그루 양쪽에 둘씩
        [[100, 0, 50], [75, 25, 99, 1], 2],  # 거꾸로 섞인 순서
        [[20], [14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26], 6],  # 큰 나무 둘레에 몰려 있다
        [[30, 60], [0, 10, 20, 40, 50, 70, 80, 90], 4],  # 간격이 모두 10
    ]
    for _ in range(7):
        tree_count = rng.randint(1, 4)
        hole_count = rng.randint(1, 12)
        trees, holes = split(rng, rng.distinct(0, rng.randint(tree_count + hole_count, 3000), tree_count + hole_count), tree_count)
        cases.append([trees, holes, rng.randint(1, hole_count)])
    return cases


def medium(rng):  # 위치가 가장 클 때: 느린 풀이(간격을 1씩 늘리기)로는 못 돌린다
    return [
        [[0], [800000000, 1], 1],  # 답이 8억
        [[400000000], [0, 800000000, 399999999, 400000001], 2],  # 양 끝에 심는다
        [[0, 800000000], [266666666, 533333333, 400000000, 1], 2],
    ]


def random_small(rng):
    tree_count = rng.randint(1, 3)
    hole_count = rng.randint(1, 7)
    trees, holes = split(rng, rng.distinct(0, rng.randint(tree_count + hole_count, 40), tree_count + hole_count), tree_count)
    return [trees, holes, rng.randint(1, hole_count)]


def large(rng, index):
    if index == 0:  # 큰 나무 5만 그루가 고르게 서 있고, 그 사이 구덩이 10만 개 가운데 절반에 심는다
        trees = [i * 16_000 + rng.randint(0, 4_000) for i in range(50_000)]
        taken = set(trees)
        holes = [x for x in rng.distinct(0, TOP, 100_100) if x not in taken][:100_000]
        return [rng.shuffle(trees), holes, 50_000]
    trees, holes = split(rng, rng.distinct(0, TOP, 100_003), 3)  # 큰 나무 셋: 답이 커서 1씩 늘리면 오래 걸린다
    return [trees, holes, 30_000]
