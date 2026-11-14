def count_until(schedules, day):
    """day일까지(그날 포함) 이루어진 점검 수."""
    total = 0
    for first, gap, times in schedules:
        if day >= first:  # 첫 점검 전이면 0번
            total += min(times, (day - first) // gap + 1)  # times번을 넘지 않는다
    return total


def solution(schedules, k):
    left = min(first for first, gap, times in schedules)
    right = max(first + (times - 1) * gap for first, gap, times in schedules)
    # 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
    while left < right:
        mid = (left + right) // 2
        if count_until(schedules, mid) >= k:
            right = mid
        else:
            left = mid + 1
    return left
