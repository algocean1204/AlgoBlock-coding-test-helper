# 틀린 까닭: 바위를 뚫을 때 지도에서 바위를 지워, 다른 길에서도 그 바위가 없는 것처럼 된다
from collections import deque


def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    seen = [[[False] * (drill + 1) for _ in range(cols)] for _ in range(rows)]
    seen[0][0][0] = True
    queue = deque([(0, 0, 0, 0)])
    while queue:
        r, c, used, count = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return count
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            next_used = used
            if mine[nr][nc] == 1:
                if used == drill:
                    continue
                mine[nr][nc] = 0  # 뚫은 바위를 지도에서 지운다
                next_used = used + 1
            if not seen[nr][nc][next_used]:
                seen[nr][nc][next_used] = True
                queue.append((nr, nc, next_used, count + 1))
    return -1
