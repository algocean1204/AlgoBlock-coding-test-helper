# 틀린 까닭: 칸 번호가 0 이상인지 확인하지 않는다(파이썬의 -1번은 반대쪽 끝 칸이라, 떨어진 웅덩이를 하나로 잇는다)
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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_r, next_c = now_r + dr, now_c + dc
                    if next_r < rows and next_c < cols and floor[next_r][next_c] == '#' and not visited[next_r][next_c]:
                        visited[next_r][next_c] = True
                        stack.append((next_r, next_c))
    return count
