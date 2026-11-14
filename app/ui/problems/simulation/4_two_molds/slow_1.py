# 느린 까닭: 더 바뀌지 않는데도 hours번(최대 10억 번)을 끝까지 돌린다
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
        # 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
        grown = [row[:] for row in board]
        for r in range(n):
            for c in range(m):
                if board[r][c] != '.':
                    continue
                a, b = count(board, r, c, 'A'), count(board, r, c, 'B')
                if a > b:
                    grown[r][c] = 'A'
                elif b > a:
                    grown[r][c] = 'B'
                elif a > 0:
                    grown[r][c] = '#'
        # 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
        result = [row[:] for row in grown]
        for r in range(n):
            for c in range(m):
                if grown[r][c] == 'A' and count(grown, r, c, 'B') >= 3:
                    result[r][c] = '#'
                elif grown[r][c] == 'B' and count(grown, r, c, 'A') >= 3:
                    result[r][c] = '#'
        board = result
    return [''.join(row) for row in board]
