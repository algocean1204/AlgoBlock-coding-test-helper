# 언어 함정: python.true_division @ "고리의 수는 n과 m 가운데 작은 값의 절반입니다"
def solution(board, k):
    n, m = len(board), len(board[0])
    result = [row[:] for row in board]
    for ring in range(min(n, m) / 2):
        top, bottom, left, right = ring, n - 1 - ring, ring, m - 1 - ring
        # 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
        cells = []
        for c in range(left, right + 1):
            cells.append((top, c))
        for r in range(top + 1, bottom + 1):
            cells.append((r, right))
        for c in range(right - 1, left - 1, -1):
            cells.append((bottom, c))
        for r in range(bottom - 1, top, -1):
            cells.append((r, left))
        values = [board[r][c] for r, c in cells]
        length = len(cells)
        shift = k % length  # 칸 수만큼 돌면 제자리로 돌아온다
        if ring % 2 == 1:
            shift = (length - shift) % length  # 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(다른 언어에서 음수의 나머지를 피한다)
        # 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
        for i in range(length):
            r, c = cells[(i + shift) % length]
            result[r][c] = values[i]
    return result
