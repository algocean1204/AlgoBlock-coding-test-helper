LARGE = 2

DAY_END = 23 * 60 + 59
EDGES = [7 * 60 + 30, 9 * 60 + 30, 17 * 60, 19 * 60]  # 할증 시간의 경계


def clock(minute):
    return f"{minute // 60:02d}:{minute % 60:02d}"


def member_rides(rng, member, count, longest, gap, idle):
    """한 회원의 겹치지 않는 기록 count개까지: [(시작, 끝, 글)]. 간격은 gap 근처가 자주 나오게 한다."""
    if rng.chance(1, 2):  # 절반은 할증 시간의 경계 근처에서 시작
        time = min(DAY_END - 1, max(0, rng.choice(EDGES) + rng.randint(-20, 10)))
    else:
        time = rng.randint(0, DAY_END - 1)
    time = min(time, DAY_END - longest)  # 첫 기록은 언제나 그날 안에 끝난다
    out = []
    for n in range(count):
        if n > 0:
            time += rng.choice([0, gap, gap + 1, rng.randint(0, gap + 3), rng.randint(0, idle)])
        end = time + rng.randint(1, longest)
        if end > DAY_END:
            break
        out.append((time, end, f"{member} {clock(time)} {clock(end)}"))
        time = end
    return out


def day(rng, plans, gap, longest=40, idle=90):
    """plans: [(회원번호, 기록 수)]. 시작 시각순으로 정렬된 올바른 rides를 만든다."""
    events = []
    for member, count in plans:
        events += member_rides(rng, member, count, longest, gap, idle)
    order = rng.shuffle(list(range(len(events))))
    events = [events[i] for i in order]
    events.sort(key=lambda event: event[0])  # 같은 회원의 기록은 시작 시각이 서로 달라 순서가 지켜진다
    return [event[2] for event in events]


def random_price(rng):
    return [rng.choice([0, 300, 500, 1000, 2000]), rng.choice([10, 50, 100, 150, 500]), rng.choice([1000, 5000, 20000, 1000000])]


def small(rng):
    cases = [
        [["1 00:00 23:59"], [0, 10, 1000000], 0],  # 하루 거의 전부: 1,439분 + 할증 240분
        [["5 23:58 23:59"], [2000, 500, 1000], 60],  # 1분, 하루 최대 요금보다 많다
        [["3 07:29 07:30", "3 07:30 07:31", "3 09:29 09:30", "3 09:30 09:31"], [0, 10, 1000000], 0],  # 할증 경계를 1분씩
        [["10 16:59 17:00", "11 17:00 17:01", "8 18:59 19:00", "9 19:00 19:01"], [0, 10, 1000000], 0],
        [["4 10:00 10:20", "4 10:25 10:40"], [1000, 100, 1000000], 5],  # 꼭 gap분 뒤: 이어 탄다
        [["4 10:00 10:20", "4 10:26 10:40"], [1000, 100, 1000000], 5],  # gap분 + 1분 뒤: 이어 타지 않는다
        [["4 10:00 10:20", "6 10:20 10:30", "4 10:40 10:50"], [1000, 100, 1000000], 15],  # 바로 앞 기록은 다른 회원
        [["2 10:00 11:00", "2 11:00 12:00", "2 12:00 13:00"], [500, 100, 9000], 0],  # 기록마다 상한을 걸면 달라진다
        [["31 08:00 08:10", "7 08:00 08:10", "300 08:00 08:10", "4 08:00 08:10"], [100, 10, 5000], 0],  # 요금이 모두 같다: 수로 본 번호 순
        [["999999 06:00 22:00", "1 06:00 22:00"], [2000, 500, 1000000], 60],
        [["12 05:00 10:00", "12 16:00 20:00"], [0, 100, 1000000], 0],  # 두 할증 시간을 모두 지난다
        [["77 07:40 07:50", "77 07:50 08:00", "77 08:30 08:31"], [1000, 10, 1000000], 30],  # 이어 탄 것이 이어진다
    ]
    cases.append([day(rng, [(str(member), rng.randint(1, 3)) for member in [3, 30, 300, 4, 40, 400, 5, 51, 512, 6000, 7]], 10), [500, 50, 2000], 10])
    for _ in range(4):
        gap = rng.choice([0, 5, 10, 30, 60])
        members = sorted({str(rng.randint(1, 10 ** rng.randint(1, 6) - 1)) for _ in range(rng.randint(1, 8))})
        cases.append([day(rng, [(member, rng.randint(1, 4)) for member in members], gap), random_price(rng), gap])
    return cases


def random_small(rng):
    gap = rng.choice([0, 3, 5, 10])
    members = rng.sample(["1", "2", "9", "10", "11", "25", "100"], rng.randint(1, 4))
    return [day(rng, [(member, rng.randint(1, 3)) for member in members], gap, 20), random_price(rng), gap]


def valid(rides, price, gap):
    unlock, per_minute, day_max = price
    if not (len(price) == 3 and 0 <= unlock <= 2000 and 10 <= per_minute <= 500 and 1000 <= day_max <= 1_000_000 and 0 <= gap <= 60):
        return False
    if not 1 <= len(rides) <= 100_000:
        return False
    last_start, last_end = -1, {}
    for ride in rides:
        words = ride.split(" ")
        if len(words) != 3:
            return False
        member, times = words[0], words[1:]
        if not (1 <= len(member) <= 6 and member.isdigit() and member[0] != "0"):
            return False
        minutes = []
        for time in times:
            if not (len(time) == 5 and time[2] == ":" and time[:2].isdigit() and time[3:].isdigit() and int(time[:2]) < 24 and int(time[3:]) < 60):
                return False
            minutes.append(int(time[:2]) * 60 + int(time[3:]))
        start, end = minutes
        if end <= start or start < last_start or start < last_end.get(member, 0):
            return False
        last_start, last_end[member] = start, end
    return True


def large(rng, index):
    if index == 0:  # 회원 5만 명이 두 번씩: 회원마다 전체를 다시 훑으면 5만 × 10만
        members = rng.distinct(1, 999999, 50_000)
        return [day(rng, [(str(member), 2) for member in members], 10, 30), [1000, 100, 1000000], 10]
    members = rng.distinct(1, 999999, 2_000)  # 회원 2,000명이 50번씩
    return [day(rng, [(str(member), 50) for member in members], 5, 12, 12), [300, 20, 50000], 5]
