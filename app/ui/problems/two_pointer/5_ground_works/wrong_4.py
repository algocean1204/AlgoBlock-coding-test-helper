# 틀린 까닭: 네 번째 모서리 (r2 + 1, c2 + 1)에 더하지 않고 빼서 부호를 틀린다(두 번 빠진 곳을 되돌리지 못하고 한 번 더 뺀다)
def solution(rows, cols, works):
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2 + 1] -= amount
        diff[r2 + 1][c1] -= amount
        diff[r2 + 1][c2 + 1] -= amount
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
