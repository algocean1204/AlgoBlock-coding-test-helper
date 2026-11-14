# 틀린 까닭: 시설마다 센 점검 수를 times번에서 자르지 않는다(일정이 끝난 뒤의 날까지 센다)
def count_until(schedules, day):
    total = 0
    for first, gap, times in schedules:
        if day >= first:
            total += (day - first) // gap + 1
    return total


def solution(schedules, k):
    left = min(first for first, gap, times in schedules)
    right = max(first + (times - 1) * gap for first, gap, times in schedules)
    while left < right:
        mid = (left + right) // 2
        if count_until(schedules, mid) >= k:
            right = mid
        else:
            left = mid + 1
    return left
