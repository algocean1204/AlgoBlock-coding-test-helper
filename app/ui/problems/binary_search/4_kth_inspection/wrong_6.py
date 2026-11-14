# 틀린 까닭: 마지막 점검일 first + (times - 1) * gap을 int(32비트)로 계산해 넘친다(Java의 int last = first + (times - 1) * gap; 을 흉내 냄)
def wrap(value):
    return (value + 2**31) % 2**32 - 2**31


def count_until(schedules, day):
    total = 0
    for first, gap, times in schedules:
        if day >= first:
            total += min(times, (day - first) // gap + 1)
    return total


def solution(schedules, k):
    left = min(first for first, gap, times in schedules)
    right = max(wrap(first + wrap((times - 1) * gap)) for first, gap, times in schedules)
    while left < right:
        mid = (left + right) // 2
        if count_until(schedules, mid) >= k:
            right = mid
        else:
            left = mid + 1
    return left
