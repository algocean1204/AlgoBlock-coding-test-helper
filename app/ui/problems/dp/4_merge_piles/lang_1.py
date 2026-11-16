# 언어 함정: python.shared_rows
def solution(piles):
    n = len(piles)
    prefix = [0] * (n + 1)  # prefix[i]: piles[0] ~ piles[i - 1]의 합
    for i in range(n):
        prefix[i + 1] = prefix[i] + piles[i]
    cost = [[0] * n] * n  # cost[i][j]: i ~ j번째 더미를 한 더미로 만드는 최소 시간
    for length in range(2, n + 1):  # 짧은 구간부터 채운다
        for i in range(n - length + 1):
            j = i + length - 1
            best = float('inf')
            for k in range(i, j):  # 마지막에 [i, k] 더미와 [k + 1, j] 더미를 합친다
                best = min(best, cost[i][k] + cost[k + 1][j])
            cost[i][j] = best + prefix[j + 1] - prefix[i]  # 마지막 합치기에 드는 시간 = 구간 전체의 자루 수
    return cost[0][n - 1]
