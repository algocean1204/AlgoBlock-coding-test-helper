# 틀린 까닭: 구간 합을 sum(piles[i:j])로 구해 끝 더미 j를 빠뜨린다
def solution(piles):
    n = len(piles)
    cost = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            best = float('inf')
            for k in range(i, j):
                best = min(best, cost[i][k] + cost[k + 1][j])
            cost[i][j] = best + sum(piles[i:j])
    return cost[0][n - 1]
