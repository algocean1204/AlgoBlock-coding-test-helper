# 틀린 까닭: 세로 길이 하나로 가로 범위까지 검사한다(가로와 세로가 다른 창고에서 틀리거나 범위를 벗어난다)
from collections import deque


def solution(floor):
    n = len(floor)
    for r in range(n):
        for c in range(len(floor[r])):
            if floor[r][c] == "S":
                start_r, start_c = r, c
    distance = {(start_r, start_c): 0}
    queue = deque([(start_r, start_c)])
    while queue:
        r, c = queue.popleft()
        if floor[r][c] == "E":
            return distance[(r, c)]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and floor[nr][nc] != "#" and (nr, nc) not in distance:
                distance[(nr, nc)] = distance[(r, c)] + 1
                queue.append((nr, nc))
    return -1
