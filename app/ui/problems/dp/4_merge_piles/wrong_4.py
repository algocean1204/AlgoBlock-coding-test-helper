# 틀린 까닭: 표를 시작 위치 순서대로 채워, 아직 구하지 않은 오른쪽 구간 [k + 1, j]의 값(0)을 쓴다(짧은 구간부터 채워야 한다)
def solution(piles):
    n = len(piles)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + piles[i]
    cost = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            best = float('inf')
            for k in range(i, j):
                best = min(best, cost[i][k] + cost[k + 1][j])
            cost[i][j] = best + prefix[j + 1] - prefix[i]
    return cost[0][n - 1]
