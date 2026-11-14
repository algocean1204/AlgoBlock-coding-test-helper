# 틀린 까닭: 방문 표시를 칸마다 하나만 둔다(드릴을 쓰고 먼저 온 길이, 드릴을 아끼고 늦게 온 길을 막는다)
from collections import deque


def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    visited = [[False] * cols for _ in range(rows)]
    visited[0][0] = True
    queue = deque([(0, 0, 0, 0)])  # 행, 열, 쓴 드릴 수, 이동 횟수
    while queue:
        r, c, used, count = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return count
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                next_used = used + mine[nr][nc]
                if next_used <= drill:
                    visited[nr][nc] = True
                    queue.append((nr, nc, next_used, count + 1))
    return -1
