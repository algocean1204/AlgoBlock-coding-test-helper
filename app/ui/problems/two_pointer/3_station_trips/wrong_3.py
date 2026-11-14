# 틀린 까닭: 합이 k와 같은지를 왼쪽을 당기기 전에만 보아, 당긴 뒤에 k가 된 구간을 놓친다
def solution(gaps, k):
    count = 0
    left = 0
    total = 0
    for right in range(len(gaps)):
        total += gaps[right]
        if total == k:
            count += 1
        while total > k:
            total -= gaps[left]
            left += 1
    return count
