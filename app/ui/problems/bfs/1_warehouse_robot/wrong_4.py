# 틀린 까닭: 출발 칸을 1로 세어 지나는 칸 수를 답한다(이동 횟수는 지나는 칸 수보다 1 적다)
from collections import deque


def solution(floor):
    rows, cols = len(floor), len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    distance = [[0] * cols for _ in range(rows)]
    distance[start_r][start_c] = 1
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        if floor[r][c] == "E":
            return distance[r][c]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and floor[nr][nc] != "#" and distance[nr][nc] == 0:
                distance[nr][nc] = distance[r][c] + 1
                queue.append((nr, nc))
    return -1
