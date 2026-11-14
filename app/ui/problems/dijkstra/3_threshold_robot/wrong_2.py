# 틀린 까닭: 턱 높이의 합이 가장 작은 길을 찾아 그 길의 가장 높은 턱을 답으로 한다(합이 작은 길이 가장 높은 턱도 낮은 것은 아니다)
import heapq


def solution(ground):
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    total = [[INF] * cols for _ in range(rows)]
    came_from = [[None] * cols for _ in range(rows)]
    total[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        t, r, c = heapq.heappop(heap)
        if t > total[r][c]:
            continue
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < rows and 0 <= nc < cols:
                new = t + abs(ground[nr][nc] - ground[r][c])
                if new < total[nr][nc]:
                    total[nr][nc] = new
                    came_from[nr][nc] = (r, c)
                    heapq.heappush(heap, (new, nr, nc))

    answer = 0
    r, c = rows - 1, cols - 1
    while came_from[r][c] is not None:
        pr, pc = came_from[r][c]
        answer = max(answer, abs(ground[r][c] - ground[pr][pc]))
        r, c = pr, pc
    return answer
