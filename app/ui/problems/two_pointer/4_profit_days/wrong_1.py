# 틀린 까닭: 3단계처럼 합이 target을 넘으면 왼쪽을 당기는 창을 쓴다(음수가 섞이면 당긴 뒤 다시 맞춰지는 기간을 놓친다)
def solution(profits, target):
    count = 0
    left = 0
    total = 0
    for right in range(len(profits)):
        total += profits[right]
        while total > target and left <= right:
            total -= profits[left]
            left += 1
        if total == target and left <= right:
            count += 1
    return count
