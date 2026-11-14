# 틀린 까닭: 가장 긴 막대를 찾지 않고 세 번째로 고른 막대가 가장 길다고 보고 비교한다
def solution(sticks):
    count = 0
    n = len(sticks)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if sticks[i] + sticks[j] > sticks[k]:
                    count += 1
    return count
