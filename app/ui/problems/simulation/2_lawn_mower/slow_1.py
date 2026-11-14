# 느린 까닭: 깎은 칸을 리스트에 모아 두고 움직일 때마다 리스트 전체에서 찾는다(명령 10만 개 × 깎은 칸 수만 개)
def solution(garden, commands):
    rows, cols = len(garden), len(garden[0])
    dr = [-1, 0, 1, 0]
    dc = [0, 1, 0, -1]
    for r in range(rows):
        for c in range(cols):
            if garden[r][c] == 'S':
                row, col = r, c
    direction = 0
    mowed = [(row, col)]
    for command in commands:
        if command == 'L':
            direction = (direction + 3) % 4
        elif command == 'R':
            direction = (direction + 1) % 4
        else:
            next_row, next_col = row + dr[direction], col + dc[direction]
            if 0 <= next_row < rows and 0 <= next_col < cols and garden[next_row][next_col] != '#':
                row, col = next_row, next_col
                if (row, col) not in mowed:
                    mowed.append((row, col))
    return len(mowed)
