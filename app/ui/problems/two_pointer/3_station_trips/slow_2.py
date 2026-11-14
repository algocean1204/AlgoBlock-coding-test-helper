# 느린 까닭: 거리가 k 이상이 되면 멈추지만, 타는 역마다 처음부터 다시 더한다(구간이 길면 역 수 × 구간 길이)
def solution(gaps, k):
    count = 0
    for a in range(len(gaps)):
        total = 0
        for b in range(a, len(gaps)):
            total += gaps[b]
            if total >= k:
                if total == k:
                    count += 1
                break
    return count
