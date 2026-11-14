def solution(ground):
    # 칸마다 '여기까지 오는 길에서 넘는 가장 높은 턱의 최솟값'을, 더 줄일 칸이 없을 때까지 모든 칸에서 이웃으로 되풀이해 줄인다
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    best = [[INF] * cols for _ in range(rows)]
    best[0][0] = 0
    changed = True
    while changed:
        changed = False
        for r in range(rows):
            for c in range(cols):
                if best[r][c] == INF:
                    continue
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < rows and 0 <= nc < cols:
                        value = max(best[r][c], abs(ground[nr][nc] - ground[r][c]))
                        if value < best[nr][nc]:
                            best[nr][nc] = value
                            changed = True
    return best[rows - 1][cols - 1]
