# 틀린 까닭: 드릴 없이 갈 수 있으면 그 거리를 답으로 한다(바위를 뚫으면 더 짧을 수 있다)
from collections import deque


def bfs(mine, drill):
    rows, cols = len(mine), len(mine[0])
    distance = [[[-1] * (drill + 1) for _ in range(cols)] for _ in range(rows)]
    distance[0][0][0] = 0
    queue = deque([(0, 0, 0)])
    while queue:
        r, c, used = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return distance[r][c][used]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                next_used = used + mine[nr][nc]
                if next_used <= drill and distance[nr][nc][next_used] == -1:
                    distance[nr][nc][next_used] = distance[r][c][used] + 1
                    queue.append((nr, nc, next_used))
    return -1


def solution(mine, drill):
    without = bfs(mine, 0)
    if without != -1:
        return without
    return bfs(mine, drill)
