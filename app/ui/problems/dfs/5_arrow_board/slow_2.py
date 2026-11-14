# 느린 까닭: 점수가 정해진 칸에 닿으면 이어 쓰지만, 고리에 갇힌 길은 점수를 적어 두지 않아 출발할 때마다 고리를 한 바퀴 다시 돈다(25만 칸이 한 고리면 25만 × 25만 번)
def solution(board):
    rows, cols = len(board), len(board[0])
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    score = {}
    total = 0
    for start_r in range(rows):
        for start_c in range(cols):
            stepped = set()
            path = []
            r, c = start_r, start_c
            while 0 <= r < rows and 0 <= c < cols and (r, c) not in stepped and (r, c) not in score:
                stepped.add((r, c))
                path.append((r, c))
                dr, dc = step[board[r][c]]
                r, c = r + dr, c + dc
            if not (0 <= r < rows and 0 <= c < cols):
                next_score = 0
            elif (r, c) in score:
                next_score = score[(r, c)]
            else:  # 이번 길에서 밟은 칸에 다시 닿았다: 출발 칸의 점수는 길의 길이지만, 아무 칸에도 적어 두지 않는다
                total += len(path)
                continue
            for back_r, back_c in reversed(path):
                next_score += 1
                score[(back_r, back_c)] = next_score
            total += score[(start_r, start_c)]
    return total
