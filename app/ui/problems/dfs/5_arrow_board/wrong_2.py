# 틀린 까닭: 밟은 칸 표시를 모든 출발이 함께 쓴다(다른 출발에서 밟은 칸에 닿아도 멈춰 버린다. 밟은 칸은 출발마다 따로 센다)
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    stepped = [[False] * cols for _ in range(rows)]
    total = 0
    for start_r in range(rows):
        for start_c in range(cols):
            r, c = start_r, start_c
            count = 0
            while 0 <= r < rows and 0 <= c < cols and not stepped[r][c]:
                stepped[r][c] = True
                count += 1
                dr, dc = step[board[r][c]]
                r, c = r + dr, c + dc
            total += count
    return total
