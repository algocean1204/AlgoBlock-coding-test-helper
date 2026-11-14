# 느린 까닭: 작업마다 직사각형 안의 칸을 하나씩 더한다(작업 3만 개 × 칸 최대 100만 개)
def solution(rows, cols, works):
    height = [[0] * cols for _ in range(rows)]
    for r1, c1, r2, c2, amount in works:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                height[r][c] += amount
    count = 0
    for r in range(rows):
        for c in range(cols):
            if height[r][c] == 0:
                count += 1
    return count
