def solution(floor):
    # 큐를 쓰지 않는다: 모든 칸의 거리를 '이웃 거리 + 1'로 더 줄어들지 않을 때까지 되풀이해 고친다
    rows, cols = len(floor), len(floor[0])
    big = rows * cols + 1
    dist = [[big] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "S":
                dist[r][c] = 0
    changed = True
    while changed:
        changed = False
        for r in range(rows):
            for c in range(cols):
                if floor[r][c] == "#":
                    continue
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < rows and 0 <= nc < cols and floor[nr][nc] != "#" and dist[nr][nc] + 1 < dist[r][c]:
                        dist[r][c] = dist[nr][nc] + 1
                        changed = True
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == "E":
                return dist[r][c] if dist[r][c] < big else -1
