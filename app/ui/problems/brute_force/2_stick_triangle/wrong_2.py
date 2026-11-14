# 틀린 까닭: 가장 긴 막대의 길이가 나머지 두 막대의 합과 같을 때도 삼각형으로 센다
def solution(sticks):
    count = 0
    n = len(sticks)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                total = sticks[i] + sticks[j] + sticks[k]
                longest = max(sticks[i], sticks[j], sticks[k])
                if longest <= total - longest:
                    count += 1
    return count
