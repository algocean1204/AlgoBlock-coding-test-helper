# 언어 함정: python.shared_rows
from collections import deque


def solution(floor):
    rows = len(floor)
    cols = len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c

    # distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
    distance = [[-1] * cols] * rows
    distance[start_r][start_c] = 0
    queue = deque([(start_r, start_c)])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while queue:
        r, c = queue.popleft()
        if floor[r][c] == "E":
            return distance[r][c]
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if floor[nr][nc] == "#" or distance[nr][nc] != -1:
                continue
            distance[nr][nc] = distance[r][c] + 1  # 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
            queue.append((nr, nc))
    return -1
