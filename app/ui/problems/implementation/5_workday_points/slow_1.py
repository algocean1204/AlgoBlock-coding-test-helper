# 느린 까닭: 날짜를 일 번호로 바꾼 뒤에도 시작일부터 끝날까지 하루씩 넘기며 평일을 센다(5만 명 × 최대 365만 일)
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def solution(staff, today):
    year_start = {}
    days = 0
    for year in range(1, 10000):
        year_start[year] = days
        days += 366 if is_leap(year) else 365

    def day_number(date):
        year, month, day = map(int, date.split("-"))
        number = year_start[year]
        for m in range(1, month):
            number += MONTH_DAYS[m - 1] + (1 if m == 2 and is_leap(year) else 0)
        return number + day - 1

    points = {}
    for team, start, end in staff:
        last = day_number(today if end == "-" else end)
        count = 0
        for number in range(day_number(start), last + 1):
            if number % 7 < 5:
                count += 1
        points[team] = points.get(team, 0) + count
    return [points[team] for team in sorted(points)]
