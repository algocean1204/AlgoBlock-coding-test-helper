# 틀린 까닭: 불이 끝내 닿지 않는 칸의 시각을 -1로 남겨 두고, 그 칸을 불이 붙은 칸처럼 막는다
from collections import deque


def solution(building):
    rows, cols = len(building), len(building[0])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    fire = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for r in range(rows):
        for c in range(cols):
            if building[r][c] == "F":
                fire[r][c] = 0
                queue.append((r, c))
            elif building[r][c] == "S":
                start_r, start_c = r, c
    while queue:
        r, c = queue.popleft()
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and building[nr][nc] != "#" and fire[nr][nc] == -1:
                fire[nr][nc] = fire[r][c] + 1
                queue.append((nr, nc))
    person = [[-1] * cols for _ in range(rows)]
    person[start_r][start_c] = 0
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols or building[nr][nc] == "#" or person[nr][nc] != -1:
                continue
            arrive = person[r][c] + 1
            if fire[nr][nc] <= arrive:
                continue
            if building[nr][nc] == "E":
                return arrive
            person[nr][nc] = arrive
            queue.append((nr, nc))
    return -1
