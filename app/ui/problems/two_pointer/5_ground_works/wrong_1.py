# 틀린 까닭: 네 모서리 가운데 (r2 + 1, c2 + 1)에 다시 더하는 표시를 빠뜨려, 오른쪽 아래 바깥 칸들이 amount만큼 덜 된다
def solution(rows, cols, works):
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2 + 1] -= amount
        diff[r2 + 1][c1] -= amount
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
