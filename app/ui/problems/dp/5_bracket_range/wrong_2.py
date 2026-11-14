# 틀린 까닭: 빼기에서 최댓값끼리, 최솟값끼리 뺀다(빼는 쪽 묶음은 가장 작아야 전체가 크고, 가장 커야 전체가 작다)
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
                    high = big[i][k] - big[k + 1][j]
                    low = small[i][k] - small[k + 1][j]
                else:
                    high = max(big[i][k], big[k + 1][j])
                    low = max(small[i][k], small[k + 1][j])
                best = max(best, high)
                worst = min(worst, low)
            big[i][j] = best
            small[i][j] = worst
    return [big[0][n - 1], small[0][n - 1]]
