# 느린 까닭: 날을 첫 점검일부터 하루씩 늘려 가며 그날까지의 점검 수를 센다(마지막 점검일이 1조 일 가까이 된다)
def solution(schedules, k):
    day = min(first for first, gap, times in schedules)
    while True:
        total = 0
        for first, gap, times in schedules:
            if day >= first:
                total += min(times, (day - first) // gap + 1)
        if total >= k:
            return day
        day += 1
