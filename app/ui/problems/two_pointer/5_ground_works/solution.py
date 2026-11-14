def solution(rows, cols, works):
    # 끝 다음 칸(r2 + 1행, c2 + 1열)에도 표시해야 하므로 한 행, 한 열씩 크게 만든다
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2 + 1] -= amount
        diff[r2 + 1][c1] -= amount
        diff[r2 + 1][c2 + 1] += amount
    # 가로로 누적: 같은 행 안에서 왼쪽 표시를 오른쪽으로 펼친다
    for r in range(rows + 1):
        for c in range(1, cols + 1):
            diff[r][c] += diff[r][c - 1]
    # 세로로 누적: 같은 열 안에서 위쪽 표시를 아래로 펼친다
    for r in range(1, rows + 1):
        for c in range(cols + 1):
            diff[r][c] += diff[r - 1][c]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if diff[r][c] == 0:
                count += 1
    return count
