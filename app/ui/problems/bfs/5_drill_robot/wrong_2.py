# 틀린 까닭: 드릴을 쓸 수 있는지 볼 때 쓰기 전 횟수로 한도를 검사해 drill + 1번까지 쓴다
from collections import deque


def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    seen = {(0, 0, 0)}
    queue = deque([(0, 0, 0, 0)])  # 행, 열, 쓴 드릴 수, 이동 횟수
    while queue:
        r, c, used, count = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return count
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if mine[nr][nc] == 1:
                if used > drill:
                    continue
                next_used = used + 1
            else:
                next_used = used
            if (nr, nc, next_used) not in seen:
                seen.add((nr, nc, next_used))
                queue.append((nr, nc, next_used, count + 1))
    return -1
