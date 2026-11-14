LARGE = 2


def clock(total):
    return f"{total // 60:02d}:{total % 60:02d}"


def small(rng):
    cases = [
        [["00:00"], 1],
        [["59:59"], 100000],                                   # k가 기록 수보다 훨씬 크다
        [["04:00", "04:00", "04:00", "04:00"], 2],             # 모두 같은 시간
        [["09:00", "08:00", "07:00", "06:00", "05:00"], 1],    # 점점 빨라진다: 모두 1위
        [["05:00", "06:00", "07:00", "08:00", "09:00"], 2],    # 점점 느려진다: 처음 두 개만
        [["01:00", "00:59", "01:01", "00:59", "01:00"], 2],    # 59초와 1분의 경계, 같은 시간
        [["02:30", "02:31", "02:29", "02:30", "02:30", "02:28"], 3],
        [["10:00", "20:00", "10:00", "30:00", "10:00", "10:00"], 3],
        [["00:10", "00:20", "00:30"], 3],                      # 기록 수와 k가 같다
    ]
    for _ in range(7):
        n = rng.randint(6, 40)
        cases.append([[clock(rng.randint(100, 112)) for _ in range(n)], rng.randint(1, 6)])
    cases.append([[clock(rng.randint(0, 3599)) for _ in range(150)], 20])
    return cases


def random_small(rng):
    n = rng.randint(1, 10)
    return [[clock(rng.randint(58, 62)) for _ in range(n)], rng.randint(1, 5)]


def large(rng, index):
    n = 100_000
    if index == 0:
        return [[clock(rng.randint(0, 3599)) for _ in range(n)], 50_000]
    # 같은 시간이 아주 많고, 시간이 조금씩 빨라져 알림이 자주 간다
    return [[clock(max(0, 3599 - i // 200 - rng.randint(0, 30))) for i in range(n)], 1_000]


def valid(records, k):
    def is_clock(text):
        return len(text) == 5 and text[2] == ":" and text[:2].isdigit() and text[3:].isdigit() and int(text[:2]) <= 59 and int(text[3:]) <= 59
    return 1 <= len(records) <= 100_000 and all(is_clock(record) for record in records) and 1 <= k <= 100_000
