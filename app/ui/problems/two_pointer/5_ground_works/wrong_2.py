# 틀린 까닭: 빼는 표시를 끝 다음 칸이 아니라 끝 칸(r2, c2)에 두어, 마지막 행과 마지막 열이 빠진다
def solution(rows, cols, works):
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2] -= amount
        diff[r2][c1] -= amount
        diff[r2][c2] += amount
    for r in range(rows + 1):
        for c in range(1, cols + 1):
            diff[r][c] += diff[r][c - 1]
    for r in range(1, rows + 1):
        for c in range(cols + 1):
            diff[r][c] += diff[r - 1][c]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if diff[r][c] == 0:
                count += 1
    return count
