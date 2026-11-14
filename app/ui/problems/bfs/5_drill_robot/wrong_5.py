# 틀린 까닭: 칸마다 기록을 하나만 두고, 같은 거리로 왔을 때만 드릴을 덜 쓴 길로 바꾼다(드릴을 쓴 길이 더 일찍 칸을 차지하면 아낀 길이 버려진다)
def solution(mine, drill):
    rows, cols = len(mine), len(mine[0])
    record = [[None] * cols for _ in range(rows)]  # 칸마다 (이동 횟수, 쓴 드릴 수) 하나
    record[0][0] = (0, 0)
    level = [(0, 0)]
    count = 0
    while level:
        if (rows - 1, cols - 1) in level:
            return count
        next_level = []
        for r, c in level:
            used = record[r][c][1]
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue
                next_used = used + mine[nr][nc]
                if next_used > drill:
                    continue
                old = record[nr][nc]
                if old is None:
                    record[nr][nc] = (count + 1, next_used)
                    next_level.append((nr, nc))
                elif old[0] == count + 1 and next_used < old[1]:
                    record[nr][nc] = (count + 1, next_used)  # 같은 거리면 드릴을 덜 쓴 쪽으로 바꾼다
        level = next_level
        count += 1
    return -1
