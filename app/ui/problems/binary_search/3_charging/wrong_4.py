# 틀린 까닭: 오른쪽 끝을 '가장 느린 충전기 × (n ÷ 충전기 수, 나머지 버림)'으로 어림해, 나머지 때문에 답이 그보다 클 때 찾지 못한다
def solution(n, chargers):
    left = 1
    right = max(chargers) * (n // len(chargers))
    while left < right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done >= n:
            right = mid
        else:
            left = mid + 1
    return left
