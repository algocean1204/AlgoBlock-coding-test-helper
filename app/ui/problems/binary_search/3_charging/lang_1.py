# 언어 함정: python.true_division
def solution(n, chargers):
    left = 1
    right = min(chargers) * n
    while left < right:
        mid = (left + right) / 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done >= n:
            right = mid
        else:
            left = mid + 1
    return left
