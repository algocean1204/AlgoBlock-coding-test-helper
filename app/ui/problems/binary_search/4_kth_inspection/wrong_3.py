# 틀린 까닭: 첫 점검일보다 이른 날에서 (day - first) // gap + 1이 0보다 작아지는 것을 막지 않는다
def count_until(schedules, day):
    total = 0
    for first, gap, times in schedules:
        total += min(times, (day - first) // gap + 1)
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
