# 틀린 까닭: 앞으로 움직일 때마다 개수를 늘려 같은 칸을 여러 번 센다(지나간 칸을 표시하지 않았다)
def solution(garden, commands):
    rows, cols = len(garden), len(garden[0])
    dr = [-1, 0, 1, 0]
    dc = [0, 1, 0, -1]
    for r in range(rows):
        for c in range(cols):
            if garden[r][c] == 'S':
                row, col = r, c
    direction = 0
    count = 1
    for command in commands:
        if command == 'L':
            direction = (direction + 3) % 4
        elif command == 'R':
            direction = (direction + 1) % 4
        else:
            next_row, next_col = row + dr[direction], col + dc[direction]
            if 0 <= next_row < rows and 0 <= next_col < cols and garden[next_row][next_col] != '#':
                row, col = next_row, next_col
                count += 1
    return count
