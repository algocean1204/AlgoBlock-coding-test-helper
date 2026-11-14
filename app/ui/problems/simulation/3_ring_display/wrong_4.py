# 틀린 까닭: 맨 바깥 고리의 칸 수로 k의 나머지를 한 번만 구해 모든 고리에 쓴다(고리마다 칸 수가 다르다)
def solution(board, k):
    n, m = len(board), len(board[0])
    result = [row[:] for row in board]
    outer = 2 * (n + m) - 4
    shift_all = k % outer
    for ring in range(min(n, m) // 2):
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
        shift = shift_all
        if ring % 2 == 1:
            shift = (length - shift) % length  # 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸
        # 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
        for i in range(length):
            r, c = cells[(i + shift) % length]
            result[r][c] = values[i]
    return result
