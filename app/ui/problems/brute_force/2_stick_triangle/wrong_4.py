# 틀린 까닭: 고르는 순서만 다른 것을 따로 센다(세 번호가 서로 다르기만 하면 모두 센다)
def solution(sticks):
    count = 0
    n = len(sticks)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i == j or j == k or i == k:
                    continue
                total = sticks[i] + sticks[j] + sticks[k]
                longest = max(sticks[i], sticks[j], sticks[k])
                if longest < total - longest:
                    count += 1
    return count
