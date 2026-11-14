# 틀린 까닭: 구간의 최댓값과 최솟값의 시작값을 0으로 둔다(구간의 값이 모두 음수이거나 모두 양수일 때 틀린다)
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
            best = 0
            worst = 0
            for k in range(i, j):
                if signs[k] == '+':
                    high = big[i][k] + big[k + 1][j]
                    low = small[i][k] + small[k + 1][j]
                elif signs[k] == '-':
                    high = big[i][k] - small[k + 1][j]
                    low = small[i][k] - big[k + 1][j]
                else:
                    high = max(big[i][k], big[k + 1][j])
                    low = max(small[i][k], small[k + 1][j])
                best = max(best, high)
                worst = min(worst, low)
            big[i][j] = best
            small[i][j] = worst
    return [big[0][n - 1], small[0][n - 1]]
