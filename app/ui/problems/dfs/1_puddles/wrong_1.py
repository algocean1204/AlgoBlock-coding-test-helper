# 틀린 까닭: 대각선으로 맞닿은 칸까지 이어진 것으로 본다(여덟 방향을 본다)
def solution(floor):
    rows, cols = len(floor), len(floor[0])
    visited = [[False] * cols for _ in range(rows)]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] != '#' or visited[r][c]:
                continue
            count += 1
            visited[r][c] = True
            stack = [(r, c)]
            while stack:
                now_r, now_c = stack.pop()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        next_r, next_c = now_r + dr, now_c + dc
                        if 0 <= next_r < rows and 0 <= next_c < cols and floor[next_r][next_c] == '#' and not visited[next_r][next_c]:
                            visited[next_r][next_c] = True
                            stack.append((next_r, next_c))
    return count
