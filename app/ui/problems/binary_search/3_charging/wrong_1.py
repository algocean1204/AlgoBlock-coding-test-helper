# 틀린 까닭: 'n대 이상'이 아니라 'n대보다 많이'(>) 충전되는지로 판정해, 답보다 긴 시간을 돌려준다
def solution(n, chargers):
    left = 1
    right = min(chargers) * n
    while left < right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done > n:
            right = mid
        else:
            left = mid + 1
    return left
