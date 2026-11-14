def solution(mine, drill):
    # 큐를 쓰지 않는다: (행, 열, 쓴 횟수)마다 최소 이동 횟수를 '이웃 + 1'로 더 줄어들지 않을 때까지 되풀이해 고친다
    rows, cols = len(mine), len(mine[0])
    big = rows * cols * (drill + 1) + 1
    best = [[[big] * (drill + 1) for _ in range(cols)] for _ in range(rows)]
    best[0][0][0] = 0
    changed = True
    while changed:
        changed = False
        for r in range(rows):
            for c in range(cols):
                for used in range(drill + 1):
                    if best[r][c][used] == big:
                        continue
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                        if 0 <= nr < rows and 0 <= nc < cols:
                            next_used = used + mine[nr][nc]
                            if next_used <= drill and best[r][c][used] + 1 < best[nr][nc][next_used]:
                                best[nr][nc][next_used] = best[r][c][used] + 1
                                changed = True
    answer = min(best[rows - 1][cols - 1])
    return -1 if answer == big else answer
