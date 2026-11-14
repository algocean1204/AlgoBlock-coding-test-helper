# 느린 까닭: 뚫을 바위 drill개를 고르는 모든 조합마다 그 바위를 지우고 BFS를 다시 한다(조합 수가 폭발한다)
from collections import deque
from itertools import combinations


def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    rocks = [(r, c) for r in range(rows) for c in range(cols) if mine[r][c] == 1]

    def shortest(opened):
        distance = [[-1] * cols for _ in range(rows)]
        distance[0][0] = 0
        queue = deque([(0, 0)])
        while queue:
            r, c = queue.popleft()
            if r == rows - 1 and c == cols - 1:
                return distance[r][c]
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and distance[nr][nc] == -1:
                    if mine[nr][nc] == 0 or (nr, nc) in opened:
                        distance[nr][nc] = distance[r][c] + 1
                        queue.append((nr, nc))
        return -1

    best = -1
    for chosen in combinations(rocks, min(drill, len(rocks))):
        got = shortest(set(chosen))
        if got != -1 and (best == -1 or got < best):
            best = got
    return best
