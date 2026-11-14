# 틀린 까닭: 첫 점검일을 빼지 않고 day // gap으로 센다(gap일마다 0일부터 점검하는 것처럼 센다)
def count_until(schedules, day):
    total = 0
    for first, gap, times in schedules:
        if day >= first:
            total += min(times, day // gap)
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
