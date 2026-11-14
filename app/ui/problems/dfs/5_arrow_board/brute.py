def solution(board):
    # 정의 그대로: 칸마다 말을 새로 올려놓고 멈출 때까지 옮겨 본다
    rows, cols = len(board), len(board[0])
    total = 0
    for start_r in range(rows):
        for start_c in range(cols):
            stepped = {(start_r, start_c)}
            r, c = start_r, start_c
            while True:
                arrow = board[r][c]
                next_r = r + (arrow == 'D') - (arrow == 'U')
                next_c = c + (arrow == 'R') - (arrow == 'L')
                if not (0 <= next_r < rows and 0 <= next_c < cols) or (next_r, next_c) in stepped:
                    break
                stepped.add((next_r, next_c))
                r, c = next_r, next_c
            total += len(stepped)
    return total
