# 언어 함정: python.shared_rows
from collections import deque


def solution(building):
    rows = len(building)
    cols = len(building[0])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
    # fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
    fire = [[-1] * cols] * rows
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

    # 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
    person = [[-1] * cols for _ in range(rows)]
    person[start_r][start_c] = 0
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if building[nr][nc] == "#" or person[nr][nc] != -1:
                continue
            arrive = person[r][c] + 1
            if fire[nr][nc] != -1 and fire[nr][nc] <= arrive:  # 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
                continue
            if building[nr][nc] == "E":
                return arrive
            person[nr][nc] = arrive
            queue.append((nr, nc))
    return -1
