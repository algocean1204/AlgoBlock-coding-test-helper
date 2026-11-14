# 틀린 까닭: 'N'(위쪽)을 행 번호가 늘어나는 쪽으로 본다(수학 좌표처럼 위를 +로 생각했다)
def solution(rows, cols, start, commands):
    move = {'N': (1, 0), 'S': (-1, 0), 'W': (0, -1), 'E': (0, 1)}
    row, col = start[0], start[1]
    for command in commands:
        dr, dc = move[command]
        next_row, next_col = row + dr, col + dc
        if 0 <= next_row < rows and 0 <= next_col < cols:
            row, col = next_row, next_col
    return [row, col]
