LARGE = 2


def random_bookings(rng, days, count, most):
    bookings = []
    for _ in range(count):
        first, last = sorted([rng.randint(1, days), rng.randint(1, days)])
        bookings.append([first, last, rng.randint(1, most)])
    return bookings


def small(rng):
    cases = [
        [1, [[1, 1, 1]]],  # 가장 작은 입력
        [1, [[1, 1, 1000], [1, 1, 1000]]],  # 가장 큰 손님 수, 같은 예약 두 개
        [5, [[5, 5, 7]]],  # 마지막 날 하루: last + 1일 칸이 필요하다
        [5, [[1, 5, 2], [1, 5, 3]]],  # 전체 기간이 겹친다
        [6, [[1, 2, 4], [3, 4, 4], [5, 6, 4]]],  # 겹치지 않고 모두 같은 값
        [6, [[1, 3, 2], [3, 6, 2]]],  # 앞 예약의 마지막 날에만 겹친다
        [10, [[2, 4, 5], [4, 7, 1], [7, 9, 5], [9, 10, 1]]],  # 끝 날마다 겹친다
        [8, [[1, 8, 1]] + [[day, day, 1] for day in range(1, 9)]],
        [100, [[1, 100, 1000]] * 60],
        [100000, [[1, 100000, 1000], [100000, 100000, 1000]]],  # 가장 긴 기간, 답이 마지막 날
        [9, [[1, 9, 3], [2, 8, 3], [3, 7, 3], [4, 6, 3], [5, 5, 3]]],  # 가운데로 갈수록 겹친다
    ]
    for _ in range(6):
        days = rng.randint(5, 30)
        cases.append([days, random_bookings(rng, days, rng.randint(3, 15), 10)])
    cases.append([200, random_bookings(rng, 200, 60, 1000)])
    return cases


def random_small(rng):
    days = rng.randint(1, 8)
    return [days, random_bookings(rng, days, rng.randint(1, 5), 5)]


def valid(days, bookings):
    return 1 <= days <= 100_000 and 1 <= len(bookings) <= 50_000 and all(
        len(b) == 3 and 1 <= b[0] <= b[1] <= days and 1 <= b[2] <= 1000 for b in bookings)


def large(rng, index):
    days = 100_000
    if index == 0:  # 예약마다 거의 전체 기간: 날을 하나씩 더하는 풀이가 가장 오래 걸린다
        bookings = [[rng.randint(1, 1000), rng.randint(days - 999, days), rng.randint(1, 1000)] for _ in range(50_000)]
        return [days, bookings]
    return [days, random_bookings(rng, days, 50_000, 1000)]
