# 틀린 까닭: 네 모서리에 표시한 뒤 가로로만 누적하고 세로 누적을 빠뜨린다
def solution(rows, cols, works):
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2 + 1] -= amount
        diff[r2 + 1][c1] -= amount
        diff[r2 + 1][c2 + 1] += amount
    for r in range(rows + 1):
        for c in range(1, cols + 1):
            diff[r][c] += diff[r][c - 1]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if diff[r][c] == 0:
                count += 1
    return count
