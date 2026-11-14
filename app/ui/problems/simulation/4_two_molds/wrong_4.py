# 틀린 까닭: 2단계를 제자리에서 바꿔, 먼저 '#'이 된 칸을 같은 단계의 다른 칸 판단에서 균으로 세지 않는다
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
        # 2단계(포위): 복사하지 않고 result 하나에서 읽고 쓴다
        result = grown
        for r in range(n):
            for c in range(m):
                if result[r][c] == 'A' and count(result, r, c, 'B') >= 3:
                    result[r][c] = '#'
                elif result[r][c] == 'B' and count(result, r, c, 'A') >= 3:
                    result[r][c] = '#'
        if result == board:  # 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
            break
        board = result
    return [''.join(row) for row in board]
