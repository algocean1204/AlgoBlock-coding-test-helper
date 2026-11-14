LARGE = 2

TEAM_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def leap(year):
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def month_days(year):
    return [31, 29 if leap(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


YEAR_START = [0, 0]  # YEAR_START[y] = y년 1월 1일의 일 번호(1년 1월 1일이 0, 월요일)
for _year in range(1, 10000):
    YEAR_START.append(YEAR_START[-1] + (366 if leap(_year) else 365))
LAST = YEAR_START[10000] - 1  # 9999-12-31


def to_number(text):
    year, month, day = int(text[:4]), int(text[5:7]), int(text[8:])
    return YEAR_START[year] + sum(month_days(year)[:month - 1]) + day - 1


def to_date(number):
    low, high = 1, 9999  # number가 든 해를 이분 탐색으로 찾는다
    while low < high:
        middle = (low + high + 1) // 2
        if YEAR_START[middle] <= number:
            low = middle
        else:
            high = middle - 1
    rest = number - YEAR_START[low]
    for month, days in enumerate(month_days(low), 1):
        if rest < days:
            return f"{low:04d}-{month:02d}-{rest + 1:02d}"
        rest -= days


ANCHORS = ["0001-01-01", "0100-02-28", "0400-02-28", "1900-02-28", "1999-12-31", "2000-02-28", "2024-02-28", "2100-02-28", "9999-12-20"]


def rows_near(rng, teams, count, center, spread, longest):
    """center일째 근처(±spread일)에서 시작하는 행 count개와 today."""
    spans = []
    for _ in range(count):
        first = min(LAST, max(0, center + rng.randint(-spread, spread)))
        spans.append((first, min(LAST, first + rng.randint(0, longest))))
    today = min(LAST, max(last for _, last in spans) + rng.randint(0, 10))
    rows = [[rng.choice(teams), to_date(first), "-" if rng.chance(1, 4) else to_date(last)] for first, last in spans]
    return [rows, to_date(today)]


def small(rng):
    cases = [
        [[["a", "0001-01-01", "0001-01-01"]], "0001-01-01"],  # 첫날, 월요일 하루
        [[["a", "0001-01-06", "0001-01-07"]], "0001-01-07"],  # 토, 일만 다녔다: 0점
        [[["z", "9999-12-31", "-"]], "9999-12-31"],  # 마지막 날 하루(금요일)
        [[["a", "1900-01-01", "-"]], "2100-12-31"],  # 200년
        [[["hr", "2100-02-22", "2100-03-08"], ["hr", "2100-03-01", "2100-03-01"]], "2100-12-31"],  # 2100년은 평년
        [[["lab", "2000-02-21", "2000-03-06"], ["lab", "2000-03-01", "2000-03-01"]], "2000-03-31"],  # 2000년은 윤년
        [[["old", "0100-02-22", "0100-03-08"], ["old", "0400-02-22", "0400-03-08"]], "0400-12-31"],  # 100년은 평년, 400년은 윤년
        [[["w", "2023-03-01", "2023-03-07"], ["w", "2023-03-04", "2023-03-16"]], "2023-03-31"],  # 7일 꼭: 수요일부터 / 13일: 토요일부터
        [[["d", "2019-06-03", "2019-06-07"], ["devops", "2019-06-08", "2019-06-09"], ["dev", "2019-06-07", "-"],
          ["de", "2019-06-10", "2019-06-10"], ["ops", "2019-06-01", "2019-06-14"]], "2019-06-14"],  # 앞부분이 같은 부서 이름, 0점 부서
        [[["tax", "1999-12-27", "-"], ["tax", "2000-01-01", "-"]], "2000-01-03"],  # today가 월요일: today도 센다
        [[["b", "2024-02-29", "2024-02-29"], ["a", "2024-03-02", "2024-03-03"], ["c", "2023-02-28", "2023-03-01"]], "2024-03-09"],
        [[["qa", "0476-09-04", "0477-09-03"], ["it", "0999-12-25", "1000-01-05"]], "1000-01-05"],  # 앞을 0으로 채운 연도
    ]
    cases.append(rows_near(rng, ["m", "n", "mn", "nm"], 12, to_number("2024-02-28"), 400, 900))
    for _ in range(5):
        cases.append(rows_near(rng, ["sales", "dev", "hr", "devops", "ops"], rng.randint(3, 15), rng.randint(0, LAST), 3000, 20000))
    return cases


def medium(rng):
    """하루씩 세는 brute.py로는 오래 걸리는 긴 기간. 답은 solution.py가 정한다."""
    cases = [
        [[["all", "0001-01-01", "-"]], "9999-12-31"],  # 가장 긴 기간 하나: 3,652,059일
        [[["x", "0001-01-01", "9999-12-31"], ["y", "0001-01-01", "9999-12-31"], ["x", "0001-01-08", "9999-12-31"]], "9999-12-31"],  # x는 y의 두 배에서 5를 뺀 값
        [[["c", "0099-03-01", "0401-02-28"], ["c", "1899-03-01", "2101-02-28"], ["d", "0001-01-01", "0001-12-31"]], "2200-01-01"],  # 100·400의 배수인 해를 여럿 지난다
    ]
    for _ in range(3):
        rows = []
        for _ in range(rng.randint(5, 30)):
            first, last = sorted([rng.randint(0, LAST), rng.randint(0, LAST)])
            rows.append([rng.choice(["sales", "dev", "hr", "devops"]), to_date(first), "-" if rng.chance(1, 4) else to_date(last)])
        cases.append([rows, to_date(LAST)])
    return cases


def random_small(rng):
    center = to_number(rng.choice(ANCHORS))
    longest = 800 if rng.chance(1, 5) else 20
    return rows_near(rng, ["a", "b", "ab"], rng.randint(1, 5), center, 15, longest)


def random_team(rng):
    return rng.word(rng.randint(1, 10), TEAM_LETTERS)


def valid(staff, today):
    def number(text):  # 올바른 "YYYY-MM-DD"이면 일 번호, 아니면 None
        if len(text) != 10 or text[4] != "-" or text[7] != "-" or not (text[:4] + text[5:7] + text[8:]).isdigit():
            return None
        year, month, day = int(text[:4]), int(text[5:7]), int(text[8:])
        if not (1 <= year <= 9999 and 1 <= month <= 12 and 1 <= day <= month_days(year)[month - 1]):
            return None
        return to_number(text)

    last = number(today)
    if last is None or not 1 <= len(staff) <= 50_000:
        return False
    for row in staff:
        if len(row) != 3:
            return False
        team, start, end = row
        if not (1 <= len(team) <= 10 and all(ch in TEAM_LETTERS for ch in team)):
            return False
        first = number(start)
        if first is None or first > last:
            return False
        if end != "-" and (number(end) is None or not first <= number(end) <= last):
            return False
    return True


def large(rng, index):
    if index == 0:  # 부서 2,000개, 기간은 고르게 무작위: 하루씩 세면 5만 행 × 평균 120만여 일
        teams = [random_team(rng) for _ in range(2_000)]
        rows = []
        for _ in range(50_000):
            first, last = sorted([rng.randint(0, LAST), rng.randint(0, LAST)])
            rows.append([rng.choice(teams), to_date(first), "-" if rng.chance(1, 5) else to_date(last)])
        return [rows, to_date(LAST)]
    # 거의 1만 년씩 다닌 4만 8천 명이 한 부서에: 합이 약 1,250억으로 32비트 int를 넘는다
    rows = []
    for n in range(50_000):
        team = "archive" if n < 48_000 else random_team(rng)
        first = rng.randint(0, 1000)
        rows.append([team, to_date(first), "-" if rng.chance(1, 3) else to_date(LAST - rng.randint(0, 1000))])
    return [rows, to_date(LAST)]
