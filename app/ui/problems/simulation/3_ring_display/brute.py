def solution(board, k):
    # 칸마다 "시계 방향으로 바로 다음 칸"을 구하는 함수로 보석을 한 칸씩 걸어서 옮긴다.
    # 고리의 칸 수도 공식 대신 한 바퀴 걸어서 센다.
    n, m = len(board), len(board[0])

    def ring_of(r, c):
        return min(r, c, n - 1 - r, m - 1 - c)

    def next_clockwise(r, c):
        g = ring_of(r, c)
        top, bottom, left, right = g, n - 1 - g, g, m - 1 - g
        if r == top and c < right:
            return r, c + 1
        if c == right and r < bottom:
            return r + 1, c
        if r == bottom and c > left:
            return r, c - 1
        return r - 1, c

    def next_counterclockwise(r, c):
        g = ring_of(r, c)
        top, bottom, left, right = g, n - 1 - g, g, m - 1 - g
        if c == left and r < bottom:
            return r + 1, c
        if r == bottom and c < right:
            return r, c + 1
        if c == right and r > top:
            return r - 1, c
        return r, c - 1

    result = [[0] * m for _ in range(n)]
    for r in range(n):
        for c in range(m):
            length, pos = 1, next_clockwise(r, c)
            while pos != (r, c):
                length += 1
                pos = next_clockwise(*pos)
            step = next_clockwise if ring_of(r, c) % 2 == 0 else next_counterclockwise
            pos = (r, c)
            for _ in range(k % length):
                pos = step(*pos)
            result[pos[0]][pos[1]] = board[r][c]
    return result
