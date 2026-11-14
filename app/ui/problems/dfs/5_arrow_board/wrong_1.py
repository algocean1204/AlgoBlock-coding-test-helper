# 틀린 까닭: 지금 길 위의 칸에 다시 닿으면 밖으로 나간 것처럼 보고 길 끝에서부터 1, 2, 3점을 매긴다(고리 위의 칸은 모두 고리 길이만큼 점수를 받아야 한다)
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    state = [[0] * cols for _ in range(rows)]
    score = [[0] * cols for _ in range(rows)]
    for start_r in range(rows):
        for start_c in range(cols):
            if state[start_r][start_c] == 2:
                continue
            path = []
            r, c = start_r, start_c
            while True:
                state[r][c] = 1
                path.append((r, c))
                dr, dc = step[board[r][c]]
                r, c = r + dr, c + dc
                if not (0 <= r < rows and 0 <= c < cols) or state[r][c] == 1:
                    next_score = 0
                    break
                if state[r][c] == 2:
                    next_score = score[r][c]
                    break
            for back_r, back_c in reversed(path):
                next_score += 1
                score[back_r][back_c] = next_score
                state[back_r][back_c] = 2
    return sum(sum(row) for row in score)
