# 느린 까닭: 불이 난 칸마다 따로 BFS를 해서 칸마다 가장 이른 시각을 고른다(불이 많으면 불 수 × 칸 수)
from collections import deque


def solution(building):
    rows, cols = len(building), len(building[0])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    big = rows * cols + 1
    fire = [[big] * cols for _ in range(rows)]
    for fr in range(rows):
        for fc in range(cols):
            if building[fr][fc] != "F":
                continue
            seen = [[-1] * cols for _ in range(rows)]
            seen[fr][fc] = 0
            queue = deque([(fr, fc)])
            while queue:
                r, c = queue.popleft()
                fire[r][c] = min(fire[r][c], seen[r][c])
                for dr, dc in moves:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and building[nr][nc] != "#" and seen[nr][nc] == -1:
                        seen[nr][nc] = seen[r][c] + 1
                        queue.append((nr, nc))
    for r in range(rows):
        for c in range(cols):
            if building[r][c] == "S":
                start_r, start_c = r, c
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
