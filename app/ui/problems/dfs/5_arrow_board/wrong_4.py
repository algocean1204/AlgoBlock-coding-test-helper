# 틀린 까닭: 재귀로 다음 칸의 점수를 구하면서 재귀 깊이 제한을 늘리지 않는다(한 줄로 길게 이어진 길에서 실행 오류가 난다)
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    state = [[0] * cols for _ in range(rows)]
    order = [[0] * cols for _ in range(rows)]
    score = [[0] * cols for _ in range(rows)]

    def walk(r, c, depth):
        """(r, c)의 점수를 정한다. 고리 안에 있으면 그 고리가 시작된 순서를, 아니면 -1을 돌려준다."""
        state[r][c] = 1
        order[r][c] = depth
        dr, dc = step[board[r][c]]
        next_r, next_c = r + dr, c + dc
        loop_from = -1
        if not (0 <= next_r < rows and 0 <= next_c < cols):
            score[r][c] = 1
        elif state[next_r][next_c] == 2:
            score[r][c] = score[next_r][next_c] + 1
        elif state[next_r][next_c] == 1:  # 고리를 찾았다
            loop_from = order[next_r][next_c]
            score[r][c] = depth - loop_from + 1
        else:
            loop_from = walk(next_r, next_c, depth + 1)
            if loop_from != -1 and depth >= loop_from:
                score[r][c] = score[next_r][next_c]  # 같은 고리 위
            else:
                loop_from = -1
                score[r][c] = score[next_r][next_c] + 1
        state[r][c] = 2
        return loop_from

    for r in range(rows):
        for c in range(cols):
            if state[r][c] == 0:
                walk(r, c, 0)
    return sum(sum(row) for row in score)
