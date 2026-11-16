# 언어 함정: python.negative_index @ "광산 밖으로는 나갈 수 없습니다"
from collections import deque


def solution(mine, drill):
    rows = len(mine)
    cols = len(mine[0])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
    # distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
    distance = [[[-1] * (drill + 1) for _ in range(cols)] for _ in range(rows)]
    distance[0][0][0] = 0
    queue = deque([(0, 0, 0)])
    while queue:
        r, c, used = queue.popleft()
        if r == rows - 1 and c == cols - 1:
            return distance[r][c][used]
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if nr >= rows or nc >= cols:
                continue
            next_used = used + mine[nr][nc]  # 바위 칸이면 드릴을 한 번 더 쓴다
            if next_used > drill:
                continue
            if distance[nr][nc][next_used] != -1:
                continue
            distance[nr][nc][next_used] = distance[r][c][used] + 1
            queue.append((nr, nc, next_used))
    return -1
