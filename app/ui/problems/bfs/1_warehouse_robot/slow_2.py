# 느린 까닭: 큐에서 꺼낼 때 방문 표시를 해서, 아직 꺼내지 않은 같은 칸이 큐에 몇 번이고 다시 들어간다(넓은 빈터를 지나면 그 수가 폭발한다)
from collections import deque


def solution(floor):
    rows, cols = len(floor), len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    visited = [[False] * cols for _ in range(rows)]
    distance = [[0] * cols for _ in range(rows)]
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        visited[r][c] = True
        if floor[r][c] == "E":
            return distance[r][c]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and floor[nr][nc] != "#" and not visited[nr][nc]:
                distance[nr][nc] = distance[r][c] + 1
                queue.append((nr, nc))
    return -1
