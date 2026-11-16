# 언어 함정: python.negative_index @ "그 칸이 정원 밖이거나 바위이면"
def solution(garden, commands):
    rows, cols = len(garden), len(garden[0])
    # 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
    dr = [-1, 0, 1, 0]
    dc = [0, 1, 0, -1]
    for r in range(rows):
        for c in range(cols):
            if garden[r][c] == 'S':
                row, col = r, c
    direction = 0
    mowed = [[False] * cols for _ in range(rows)]
    mowed[row][col] = True
    count = 1
    for command in commands:
        if command == 'L':
            direction = (direction + 3) % 4  # 왼쪽으로 한 번 = 오른쪽으로 세 번(-1 대신 +3: Java·C++ 등에서는 음수의 나머지가 음수다)
        elif command == 'R':
            direction = (direction + 1) % 4
        else:
            next_row, next_col = row + dr[direction], col + dc[direction]
            if next_row < rows and next_col < cols and garden[next_row][next_col] != '#':
                row, col = next_row, next_col
                if not mowed[row][col]:
                    mowed[row][col] = True
                    count += 1
    return count
