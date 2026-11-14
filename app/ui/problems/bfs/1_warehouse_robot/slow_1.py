# 느린 까닭: DFS로 갈 수 있는 길을 모두 따라가 보며 가장 짧은 것을 고른다(길의 수가 칸 수에 대해 기하급수로 늘어난다)
import sys

sys.setrecursionlimit(100_000)


def solution(floor):
    rows, cols = len(floor), len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    visited = [[False] * cols for _ in range(rows)]
    best = [-1]

    def dfs(r, c, count):
        if best[0] != -1 and count >= best[0]:
            return
        if floor[r][c] == "E":
            best[0] = count
            return
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and floor[nr][nc] != "#" and not visited[nr][nc]:
                visited[nr][nc] = True
                dfs(nr, nc, count + 1)
                visited[nr][nc] = False

    visited[start_r][start_c] = True
    dfs(start_r, start_c, 0)
    return best[0]
