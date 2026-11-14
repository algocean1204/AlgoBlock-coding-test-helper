from datetime import date, timedelta


def solution(staff, today):
    # 표준 라이브러리의 달력(그레고리력)으로 하루씩 넘기며 평일을 센다(solution.py는 손으로 만든 달력과 7일 묶음을 쓴다)
    assert date(1, 1, 1).weekday() == 0  # 문제의 "1년 1월 1일은 월요일"과 맞는지
    points = {}
    for team, start, end in staff:
        day = date.fromisoformat(start)
        last = date.fromisoformat(today if end == "-" else end)
        count = 0
        while True:
            if day.weekday() < 5:  # 월요일 0 … 금요일 4
                count += 1
            if day == last:  # 9999-12-31 다음 날은 date로 만들 수 없으므로 넘기기 전에 멈춘다
                break
            day += timedelta(days=1)
        points[team] = points.get(team, 0) + count
    return [points[team] for team in sorted(points)]
