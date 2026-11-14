# 틀린 까닭: '^'의 가장 작은 값을 양쪽의 가장 작은 값 가운데 작은 쪽으로 구한다(작은 값끼리 견준 큰 쪽이어야 한다)
def solution(values, signs):
    n = len(values)
    big = [[0] * n for _ in range(n)]
    small = [[0] * n for _ in range(n)]
    for i in range(n):
        big[i][i] = values[i]
        small[i][i] = values[i]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            best = float('-inf')
            worst = float('inf')
            for k in range(i, j):
                if signs[k] == '+':
                    high = big[i][k] + big[k + 1][j]
                    low = small[i][k] + small[k + 1][j]
                elif signs[k] == '-':
                    high = big[i][k] - small[k + 1][j]
                    low = small[i][k] - big[k + 1][j]
                else:
                    high = max(big[i][k], big[k + 1][j])
                    low = min(small[i][k], small[k + 1][j])
                best = max(best, high)
                worst = min(worst, low)
            big[i][j] = best
            small[i][j] = worst
    return [big[0][n - 1], small[0][n - 1]]
