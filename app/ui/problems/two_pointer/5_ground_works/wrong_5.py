# 틀린 까닭: 가로·세로를 한 번에 누적하며 위 칸과 왼쪽 칸을 더하고, 두 번 더해진 왼쪽 위 칸을 빼지 않는다
def solution(rows, cols, works):
    diff = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r1, c1, r2, c2, amount in works:
        diff[r1][c1] += amount
        diff[r1][c2 + 1] -= amount
        diff[r2 + 1][c1] -= amount
        diff[r2 + 1][c2 + 1] += amount
    height = [[0] * cols for _ in range(rows)]
    count = 0
    for r in range(rows):
        for c in range(cols):
            height[r][c] = diff[r][c]
            if r > 0:
                height[r][c] += height[r - 1][c]
            if c > 0:
                height[r][c] += height[r][c - 1]
            if height[r][c] == 0:
                count += 1
    return count
