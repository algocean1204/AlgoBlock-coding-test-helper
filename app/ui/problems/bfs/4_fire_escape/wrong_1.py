# 틀린 까닭: 불을 무시하고 가장 가까운 비상구까지의 거리만 구한다
from collections import deque


def solution(building):
    rows, cols = len(building), len(building[0])
    for r in range(rows):
        for c in range(cols):
            if building[r][c] == "S":
                start_r, start_c = r, c
    person = [[-1] * cols for _ in range(rows)]
    person[start_r][start_c] = 0
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        if building[r][c] == "E":
            return person[r][c]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and building[nr][nc] != "#" and person[nr][nc] == -1:
                person[nr][nc] = person[r][c] + 1
                queue.append((nr, nc))
    return -1
