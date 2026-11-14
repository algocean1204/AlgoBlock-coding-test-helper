# 틀린 까닭: 2단계(포위)를 1단계(번식)보다 먼저 적용한다
def solution(dish, hours):
    n, m = len(dish), len(dish[0])
    board = [list(line) for line in dish]

    def count(grid, r, c, mold):
        """grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수."""
        total = 0
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < n and 0 <= nc < m and grid[nr][nc] == mold:
                total += 1
        return total

    for _ in range(hours):
        # 2단계(포위)를 먼저: board를 보고 surrounded에 적는다
        surrounded = [row[:] for row in board]
        for r in range(n):
            for c in range(m):
                if board[r][c] == 'A' and count(board, r, c, 'B') >= 3:
                    surrounded[r][c] = '#'
                elif board[r][c] == 'B' and count(board, r, c, 'A') >= 3:
                    surrounded[r][c] = '#'
        # 1단계(번식)를 나중에: surrounded를 보고 result에 적는다
        result = [row[:] for row in surrounded]
        for r in range(n):
            for c in range(m):
                if surrounded[r][c] != '.':
                    continue
                a, b = count(surrounded, r, c, 'A'), count(surrounded, r, c, 'B')
                if a > b:
                    result[r][c] = 'A'
                elif b > a:
                    result[r][c] = 'B'
                elif a > 0:
                    result[r][c] = '#'
        if result == board:  # 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
            break
        board = result
    return [''.join(row) for row in board]
