LARGE = 2


def make(rng, n, longest, latest, booked_count):
    """주문 n개: 찾으러 오는 시각 1~latest, 만드는 시간 1~longest, 꼭 받아야 하는 주문 booked_count개."""
    pickup = [rng.randint(1, latest) for _ in range(n)]
    minutes = [rng.randint(1, longest) for _ in range(n)]
    booked = rng.sample(list(range(n)), booked_count)
    return [pickup, minutes, booked]


def small(rng):
    cases = [
        [[1], [1], []],  # 가장 작은 입력
        [[1], [2], []],  # 하나도 받을 수 없다: [0, 0]
        [[1], [2], [0]],  # 꼭 받아야 하는데 늦는다: [-1, -1]
        [[2000000000], [30000], [0]],  # 가장 큰 값
        [[2, 4], [2, 2], []],  # 다 만든 시각이 찾으러 오는 시각과 같다
        [[6, 6, 6, 6], [3, 2, 4, 1], []],  # 찾으러 오는 시각이 모두 같다
        [[2, 5, 5], [1, 5, 1], []],  # 되무를 것은 가장 오래 걸리는 주문
        [[5, 5, 5], [5, 1, 1], []],  # 먼저 받은 긴 주문을 되물러야 한다
        [[5, 6, 8], [5, 2, 2], [1, 2]],  # 꼭 받아야 하는 주문이 들어와도 긴 주문 하나만 되무르면 된다
        [[3, 4, 6, 12], [2, 2, 2, 10], [3]],  # 꼭 받아야 하는 긴 주문 때문에 둘을 되무른다
        [[4, 6, 7, 9], [3, 3, 1, 4], [0, 3]],  # 예약끼리는 되지만 예약이 아닌 것을 모두 되물러야 한다
        [[4, 4, 9], [3, 3, 2], [1, 0]],  # 예약 둘이 함께 들어갈 수 없다
        [[9, 4, 6], [2, 4, 3], []],  # 개수가 같으면 일찍 끝나는 쪽을 고른다
        [[10, 10, 10, 10], [1, 2, 3, 4], [3, 2, 1, 0]],  # 모두 예약이고 모두 지킬 수 있다
        [[12, 5, 6, 8, 10], [10, 3, 3, 3, 3], [4]],  # 긴 주문 하나보다 짧은 주문 여럿
        [[9, 3, 4, 8, 9], [7, 1, 2, 6, 1], [0]],  # 예약이 가장 긴 주문이라 되무를 수 없다
    ]
    for _ in range(4):
        n = rng.randint(6, 12)
        cases.append(make(rng, n, 8, 30, rng.randint(0, 3)))
    return cases


def valid(pickup, minutes, booked):
    n = len(pickup)
    return (1 <= n <= 80_000 and len(minutes) == n and len(booked) <= n and len(set(booked)) == len(booked)
            and all(1 <= p <= 2_000_000_000 for p in pickup) and all(1 <= m <= 30_000 for m in minutes)
            and all(0 <= b < n for b in booked))


def random_small(rng):
    n = rng.randint(1, 8)
    return make(rng, n, 6, rng.randint(5, 25), rng.randint(0, min(3, n)))


def large(rng, index):
    n = 80_000
    if index == 0:
        # 오래 걸리는 주문들이 비슷한 시각에 찾으러 온다: 받은 주문 수만 개를 둔 채 되무르기를 수만 번 되풀이한다
        pickup = [rng.randint(400_000_000, 420_000_000) for _ in range(n)]
        minutes = [rng.randint(8_000, 30_000) for _ in range(n)]
        booked = rng.sample(list(range(n)), 2_000)
        for i in booked:
            minutes[i] = rng.randint(1, 50)  # 짧은 예약은 언제나 들어간다
        return [pickup, minutes, booked]
    # 예약이 많이 섞여 있고, 늦게 오는 예약이 들어올 때마다 여럿을 되무른다
    pickup = [rng.randint(200_000_000, 230_000_000) for _ in range(n)]
    minutes = [rng.randint(5_000, 30_000) for _ in range(n)]
    booked = rng.sample(list(range(n)), 20_000)
    for i in booked:
        minutes[i] = rng.randint(1, 3_000)
    return [pickup, minutes, booked]
