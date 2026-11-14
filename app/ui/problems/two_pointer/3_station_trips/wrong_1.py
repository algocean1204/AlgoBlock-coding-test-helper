# 틀린 까닭: 합이 k를 넘을 때 왼쪽을 한 번만(if로) 당겨, 여러 칸을 당겨야 하는 경우를 놓친다
def solution(gaps, k):
    count = 0
    left = 0
    total = 0
    for right in range(len(gaps)):
        total += gaps[right]
        if total > k:
            total -= gaps[left]
            left += 1
        if total == k:
            count += 1
    return count
