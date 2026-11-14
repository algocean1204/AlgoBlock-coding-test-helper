# 틀린 까닭: 고리를 찾으면 고리로 들어가기 전 칸까지 길 위의 모든 칸에 같은 점수(길 전체의 칸 수)를 준다(고리 밖의 칸은 고리에서 멀수록 점수가 크다)
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
                if not (0 <= r < rows and 0 <= c < cols):
                    next_score = 0
                    break
                if state[r][c] == 2:
                    next_score = score[r][c]
                    break
                if state[r][c] == 1:
                    for loop_r, loop_c in path:
                        score[loop_r][loop_c] = len(path)
                        state[loop_r][loop_c] = 2
                    path = []
                    break
            for back_r, back_c in reversed(path):
                next_score += 1
                score[back_r][back_c] = next_score
                state[back_r][back_c] = 2
    return sum(sum(row) for row in score)
