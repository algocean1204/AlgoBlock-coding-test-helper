# 느린 까닭: 출발 칸마다 말을 처음부터 끝까지 따로 옮겨 본다(길 하나가 25만 칸이면 25만 × 25만 번)
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    total = 0
    for start_r in range(rows):
        for start_c in range(cols):
            stepped = set()
            r, c = start_r, start_c
            while 0 <= r < rows and 0 <= c < cols and (r, c) not in stepped:
                stepped.add((r, c))
                dr, dc = step[board[r][c]]
                r, c = r + dr, c + dc
            total += len(stepped)
    return total
