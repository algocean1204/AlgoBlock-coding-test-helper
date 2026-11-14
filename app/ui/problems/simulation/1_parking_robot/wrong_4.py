# 틀린 까닭: 밖으로 나가는 명령을 만나면 남은 명령을 모두 멈춘다(그 명령만 건너뛰어야 한다)
def solution(rows, cols, start, commands):
    move = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}
    row, col = start[0], start[1]
    for command in commands:
        dr, dc = move[command]
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < rows and 0 <= next_col < cols):
            break
        row, col = next_row, next_col
    return [row, col]
