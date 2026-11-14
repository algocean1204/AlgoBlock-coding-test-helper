# 틀린 까닭: 도착 칸에서 드릴을 0번 쓴 상태와 다 쓴 상태만 보고 답을 고른다(드릴이 남은 채 도착한 상태를 놓친다)
from collections import deque


def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    distance = [[[-1] * (drill + 1) for _ in range(cols)] for _ in range(rows)]
    distance[0][0][0] = 0
    queue = deque([(0, 0, 0)])
    while queue:
        r, c, used = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                next_used = used + mine[nr][nc]
                if next_used <= drill and distance[nr][nc][next_used] == -1:
                    distance[nr][nc][next_used] = distance[r][c][used] + 1
                    queue.append((nr, nc, next_used))
    end = distance[rows - 1][cols - 1]
    found = [d for d in (end[0], end[drill]) if d != -1]
    return min(found) if found else -1
