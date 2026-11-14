# 느린 까닭: 우선순위 큐 없이 매번 모든 칸을 훑어 가장 높은 턱이 가장 낮은 칸을 찾는다(칸이 9만 개면 9만 × 9만 번)
def solution(ground):
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    effort = [[INF] * cols for _ in range(rows)]
    done = [[False] * cols for _ in range(rows)]
    effort[0][0] = 0
    while True:
        r, c = -1, -1
        for i in range(rows):
            for j in range(cols):
                if not done[i][j] and (r == -1 or effort[i][j] < effort[r][c]):
                    r, c = i, j
        if r == rows - 1 and c == cols - 1:
            return effort[r][c]
        done[r][c] = True
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < rows and 0 <= nc < cols:
                new = max(effort[r][c], abs(ground[nr][nc] - ground[r][c]))
                if new < effort[nr][nc]:
                    effort[nr][nc] = new
