MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def solution(staff, today):
    # 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
    year_start = {}
    days = 0
    for year in range(1, 10000):
        year_start[year] = days
        days += 366 if is_leap(year) else 365

    def day_number(date):
        # "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
        year, month, day = map(int, date.split("-"))
        number = year_start[year]
        for m in range(1, month):  # 그해에 지나간 달의 날 수
            number += MONTH_DAYS[m - 1]
            if m == 2 and is_leap(year):
                number += 1
        return number + day - 1

    def weekdays(first, last):
        # first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
        total = last - first + 1
        weeks = total // 7
        count = weeks * 5  # 7일 묶음마다 평일 5일
        for number in range(first + weeks * 7, last + 1):  # 남은 6일 이하는 하나씩 본다
            if number % 7 < 5:
                count += 1
        return count

    today_number = day_number(today)
    points = {}
    for team, start, end in staff:
        last = today_number if end == "-" else day_number(end)
        points[team] = points.get(team, 0) + weekdays(day_number(start), last)
    return [points[team] for team in sorted(points)]
