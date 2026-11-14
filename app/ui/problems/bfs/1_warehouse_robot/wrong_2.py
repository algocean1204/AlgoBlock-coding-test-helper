# 틀린 까닭: 오른쪽과 아래로만 움직여 본다(위나 왼쪽으로 돌아가야 하는 길을 놓친다)
from collections import deque


def solution(floor):
    rows, cols = len(floor), len(floor[0])
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    distance = [[-1] * cols for _ in range(rows)]
    distance[start_r][start_c] = 0
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        if floor[r][c] == "E":
            return distance[r][c]
        for dr, dc in ((1, 0), (0, 1)):
            nr, nc = r + dr, c + dc
            if nr < rows and nc < cols and floor[nr][nc] != "#" and distance[nr][nc] == -1:
                distance[nr][nc] = distance[r][c] + 1
                queue.append((nr, nc))
    return -1
