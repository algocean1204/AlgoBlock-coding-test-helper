# 틀린 까닭: 오른쪽과 아래로만 옮겨 가는 DP로 푼다(위나 왼쪽으로 돌아가야 하는, 턱이 더 낮은 길을 놓친다)
def solution(ground):
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    best = [[INF] * cols for _ in range(rows)]
    best[0][0] = 0
    for r in range(rows):
        for c in range(cols):
            if r > 0:
                best[r][c] = min(best[r][c], max(best[r - 1][c], abs(ground[r][c] - ground[r - 1][c])))
            if c > 0:
                best[r][c] = min(best[r][c], max(best[r][c - 1], abs(ground[r][c] - ground[r][c - 1])))
    return best[rows - 1][cols - 1]
