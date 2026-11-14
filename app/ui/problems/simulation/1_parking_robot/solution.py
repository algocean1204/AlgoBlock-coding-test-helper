def solution(rows, cols, start, commands):
    move = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}
    row, col = start[0], start[1]
    for command in commands:
        dr, dc = move[command]
        next_row, next_col = row + dr, col + dc
        if 0 <= next_row < rows and 0 <= next_col < cols:
            row, col = next_row, next_col
    return [row, col]
