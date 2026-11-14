# 틀린 까닭: DFS로 처음 닿은 길의 이동 횟수를 답으로 한다(처음 찾은 길이 가장 짧다는 보장이 없다)
import sys

sys.setrecursionlimit(100_000)


def solution(floor):
    rows, cols = len(floor), len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    visited = [[False] * cols for _ in range(rows)]

    def dfs(r, c, count):
        if floor[r][c] == "E":
            return count
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and floor[nr][nc] != "#" and not visited[nr][nc]:
                visited[nr][nc] = True
                found = dfs(nr, nc, count + 1)
                if found != -1:
                    return found
        return -1

    visited[start_r][start_c] = True
    return dfs(start_r, start_c, 0)
