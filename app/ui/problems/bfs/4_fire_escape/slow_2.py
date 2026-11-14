# 느린 까닭: 1분마다 지도 전체를 다시 훑어 불을 퍼뜨린다(대피가 오래 걸리면 분 수 × 칸 수)
def solution(building):
    rows, cols = len(building), len(building[0])
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    burning = [[building[r][c] == "F" for c in range(cols)] for r in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    frontier = []
    for r in range(rows):
        for c in range(cols):
            if building[r][c] == "S":
                visited[r][c] = True
                frontier.append((r, c))
    minute = 0
    while frontier:
        minute += 1
        spread = []
        for r in range(rows):
            for c in range(cols):
                if burning[r][c]:
                    for dr, dc in moves:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and building[nr][nc] != "#" and not burning[nr][nc]:
                            spread.append((nr, nc))
        for r, c in spread:
            burning[r][c] = True
        next_frontier = []
        for r, c in frontier:
            for dr, dc in moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and building[nr][nc] != "#" and not burning[nr][nc] and not visited[nr][nc]:
                    if building[nr][nc] == "E":
                        return minute
                    visited[nr][nc] = True
                    next_frontier.append((nr, nc))
        frontier = next_frontier
    return -1
