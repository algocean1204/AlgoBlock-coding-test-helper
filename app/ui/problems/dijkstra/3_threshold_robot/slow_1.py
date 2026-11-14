# 느린 까닭: 답이 될 수 있는 턱 높이를 작은 것부터 하나씩 정해 놓고, 그 이하의 걸음만으로 닿는지 매번 BFS로 확인한다(후보가 수만 개 × 칸 9만 개)
from collections import deque


def solution(ground):
    rows, cols = len(ground), len(ground[0])
    candidates = {0}
    for r in range(rows):
        for c in range(cols):
            if r + 1 < rows:
                candidates.add(abs(ground[r + 1][c] - ground[r][c]))
            if c + 1 < cols:
                candidates.add(abs(ground[r][c + 1] - ground[r][c]))

    for limit in sorted(candidates):
        seen = [[False] * cols for _ in range(rows)]
        seen[0][0] = True
        queue = deque([(0, 0)])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < rows and 0 <= nc < cols and not seen[nr][nc]:
                    if abs(ground[nr][nc] - ground[r][c]) <= limit:
                        seen[nr][nc] = True
                        queue.append((nr, nc))
        if seen[rows - 1][cols - 1]:
            return limit
