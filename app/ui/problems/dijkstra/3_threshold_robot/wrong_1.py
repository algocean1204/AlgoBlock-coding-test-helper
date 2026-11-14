# 틀린 까닭: 길의 값을 넘는 턱 높이의 합으로 계산한다(가장 높은 턱이어야 한다)
import heapq


def solution(ground):
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    total = [[INF] * cols for _ in range(rows)]
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
                    heapq.heappush(heap, (new, nr, nc))
    return total[rows - 1][cols - 1]
