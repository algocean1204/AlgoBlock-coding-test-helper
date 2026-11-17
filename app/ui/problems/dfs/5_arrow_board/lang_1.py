# 언어 함정: python.shared_rows
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    NEW, ON_PATH, DONE = 0, 1, 2  # 아직 안 감 / 지금 걷는 길 위 / 점수가 정해짐
    state = [[NEW] * cols] * rows
    order = [[0] * cols for _ in range(rows)]  # 지금 길에서 몇 번째로 밟은 칸인가
    score = [[0] * cols for _ in range(rows)]
    for start_r in range(rows):
        for start_c in range(cols):
            if state[start_r][start_c] == DONE:
                continue
            # 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
            path = []
            r, c = start_r, start_c
            while True:
                state[r][c] = ON_PATH
                order[r][c] = len(path)
                path.append((r, c))
                dr, dc = step[board[r][c]]
                r, c = r + dr, c + dc
                if not (0 <= r < rows and 0 <= c < cols):
                    next_score = 0  # 밖이다: 더 밟을 칸이 없다
                    break
                if state[r][c] == DONE:
                    next_score = score[r][c]  # 답을 아는 칸: 더 걷지 않고 이어 쓴다
                    break
                if state[r][c] == ON_PATH:
                    # 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
                    first = order[r][c]
                    length = len(path) - first
                    for loop_r, loop_c in path[first:]:
                        score[loop_r][loop_c] = length
                        state[loop_r][loop_c] = DONE
                    path = path[:first]  # 남은 것은 고리로 들어가기 전의 칸들
                    next_score = length
                    break
            # 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
            for back_r, back_c in reversed(path):
                next_score += 1
                score[back_r][back_c] = next_score
                state[back_r][back_c] = DONE
    total = 0
    for row in score:
        total += sum(row)
    return total
