# 틀린 까닭: 세로와 가로를 바꿔 행을 cols와, 열을 rows와 비교한다(정사각형이 아니면 틀린다)
def solution(rows, cols, start, commands):
    move = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}
    row, col = start[0], start[1]
    for command in commands:
        dr, dc = move[command]
        next_row, next_col = row + dr, col + dc
        if 0 <= next_row < cols and 0 <= next_col < rows:
            row, col = next_row, next_col
    return [row, col]
