# 언어 함정: python.negative_index @ "격자 밖으로는 나갈 수 없습니다"
import heapq


def solution(ground):
    rows, cols = len(ground), len(ground[0])
    INF = float("inf")
    highest = [[INF] * cols for _ in range(rows)]  # 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
    highest[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        h, r, c = heapq.heappop(heap)
        if h > highest[r][c]:
            continue
        if r == rows - 1 and c == cols - 1:
            return h
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nr < rows and nc < cols:
                ledge = abs(ground[nr][nc] - ground[r][c])
                new = max(h, ledge)  # 합이 아니라 가장 높은 턱
                if new < highest[nr][nc]:
                    highest[nr][nc] = new
                    heapq.heappush(heap, (new, nr, nc))
    return highest[rows - 1][cols - 1]
