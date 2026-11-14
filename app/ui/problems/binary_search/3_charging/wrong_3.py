# 틀린 까닭: 반복이 끝났을 때 마지막으로 확인한 mid를 답으로 돌려준다(그 mid는 안 되는 시간일 수 있다)
def solution(n, chargers):
    left = 1
    right = min(chargers) * n
    answer = right
    while left <= right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done >= n:
            right = mid - 1
        else:
            left = mid + 1
        answer = mid
    return answer
