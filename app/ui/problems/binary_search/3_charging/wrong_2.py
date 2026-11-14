# 틀린 까닭: 되는 시간(mid)을 찾았을 때 오른쪽 끝을 mid - 1로 줄여, 답이던 mid를 범위에서 버린다
def solution(n, chargers):
    left = 1
    right = min(chargers) * n
    while left < right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done >= n:
            right = mid - 1
        else:
            left = mid + 1
    return left
