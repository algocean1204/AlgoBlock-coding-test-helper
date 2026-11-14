# 틀린 까닭: 큐에 넣을 때 방문 표시를 해서, 나중에 찾은 턱이 더 낮은 길로 고치지 못한다
import heapq


def solution(ground):
    rows, cols = len(ground), len(ground[0])
    effort = [[0] * cols for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    visited[0][0] = True
    heap = [(0, 0, 0)]
    while heap:
        e, r, c = heapq.heappop(heap)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                visited[nr][nc] = True
                effort[nr][nc] = max(e, abs(ground[nr][nc] - ground[r][c]))
                heapq.heappush(heap, (effort[nr][nc], nr, nc))
    return effort[rows - 1][cols - 1]
