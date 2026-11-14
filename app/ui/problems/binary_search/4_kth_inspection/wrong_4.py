# 틀린 까닭: 그날까지의 점검이 딱 k번인 날을 만나면 바로 돌려준다(점검이 없는 날일 수 있다)
def count_until(schedules, day):
    total = 0
    for first, gap, times in schedules:
        if day >= first:
            total += min(times, (day - first) // gap + 1)
    return total


def solution(schedules, k):
    left = min(first for first, gap, times in schedules)
    right = max(first + (times - 1) * gap for first, gap, times in schedules)
    while left < right:
        mid = (left + right) // 2
        count = count_until(schedules, mid)
        if count == k:
            return mid
        if count > k:
            right = mid
        else:
            left = mid + 1
    return left
