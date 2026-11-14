# 느린 까닭: 타는 역마다 내리는 역을 끝까지 하나씩 늘려 본다(역 10만 개면 약 50억 쌍)
def solution(gaps, k):
    count = 0
    for a in range(len(gaps)):
        total = 0
        for b in range(a, len(gaps)):
            total += gaps[b]
            if total == k:
                count += 1
    return count
