# 느린 까닭: 진열대를 한 칸씩 정말로 k번 돌린다(k가 1억이면 1억 번 × 칸 수)
def solution(board, k):
    n, m = len(board), len(board[0])
    rings = []
    for ring in range(min(n, m) // 2):
        top, bottom, left, right = ring, n - 1 - ring, ring, m - 1 - ring
        cells = []
        for c in range(left, right + 1):
            cells.append((top, c))
        for r in range(top + 1, bottom + 1):
            cells.append((r, right))
        for c in range(right - 1, left - 1, -1):
            cells.append((bottom, c))
        for r in range(bottom - 1, top, -1):
            cells.append((r, left))
        rings.append(cells)
    for _ in range(k):
        new_board = [row[:] for row in board]
        for ring, cells in enumerate(rings):
            length = len(cells)
            for i in range(length):
                r, c = cells[i]
                if ring % 2 == 0:
                    nr, nc = cells[(i + 1) % length]
                else:
                    nr, nc = cells[(i - 1) % length]
                new_board[nr][nc] = board[r][c]
        board = new_board
    return board
