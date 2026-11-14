# 틀린 까닭: 출발 칸을 표시하지 않고 0개에서 시작해, 움직여서 처음 밟은 칸만 센다
def solution(garden, commands):
    rows, cols = len(garden), len(garden[0])
    dr = [-1, 0, 1, 0]
    dc = [0, 1, 0, -1]
    for r in range(rows):
        for c in range(cols):
            if garden[r][c] == 'S':
                row, col = r, c
    direction = 0
    mowed = [[False] * cols for _ in range(rows)]
    count = 0
    for command in commands:
        if command == 'L':
            direction = (direction + 3) % 4
        elif command == 'R':
            direction = (direction + 1) % 4
        else:
            next_row, next_col = row + dr[direction], col + dc[direction]
            if 0 <= next_row < rows and 0 <= next_col < cols and garden[next_row][next_col] != '#':
                row, col = next_row, next_col
                if not mowed[row][col]:
                    mowed[row][col] = True
                    count += 1
    return count
