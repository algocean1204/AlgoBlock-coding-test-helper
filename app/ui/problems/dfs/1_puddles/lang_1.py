# 언어 함정: python.shared_rows
def solution(floor):
    rows, cols = len(floor), len(floor[0])
    visited = [[False] * cols] * rows
    count = 0
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] != '#' or visited[r][c]:
                continue
            # 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
            count += 1
            visited[r][c] = True
            stack = [(r, c)]
            while stack:
                now_r, now_c = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_r, next_c = now_r + dr, now_c + dc
                    if not (0 <= next_r < rows and 0 <= next_c < cols):
                        continue  # 바닥 밖
                    if floor[next_r][next_c] == '#' and not visited[next_r][next_c]:
                        visited[next_r][next_c] = True
                        stack.append((next_r, next_c))
    return count
