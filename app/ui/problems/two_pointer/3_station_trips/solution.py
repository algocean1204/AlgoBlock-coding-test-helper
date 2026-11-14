def solution(gaps, k):
    count = 0
    left = 0
    total = 0  # gaps[left]부터 gaps[right]까지의 합 = left번 역에서 right + 1번 역까지의 거리
    for right in range(len(gaps)):
        total += gaps[right]
        # 거리가 모두 양수라 왼쪽을 당기면 합이 줄어든다. k 이하가 될 때까지 당긴다
        while total > k:
            total -= gaps[left]
            left += 1
        if total == k:
            count += 1
    return count
