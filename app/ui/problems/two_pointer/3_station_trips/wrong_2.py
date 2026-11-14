# 틀린 까닭: 합이 k를 넘으면 창을 버리고 지금 칸부터 새로 시작해, 그 사이 역에서 타는 구간을 놓친다
def solution(gaps, k):
    count = 0
    total = 0
    for right in range(len(gaps)):
        total += gaps[right]
        if total > k:
            total = gaps[right]
        if total == k:
            count += 1
    return count
