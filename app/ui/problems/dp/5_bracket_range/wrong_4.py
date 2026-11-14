# 틀린 까닭: 표를 시작 위치 순서대로 채워 아직 구하지 않은 오른쪽 구간의 값(0)을 쓴다(짧은 구간부터 채워야 한다)
def solution(values, signs):
    n = len(values)
    big = [[0] * n for _ in range(n)]
    small = [[0] * n for _ in range(n)]
    for i in range(n):
        big[i][i] = values[i]
        small[i][i] = values[i]
    for i in range(n):
        for j in range(i + 1, n):
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
                    low = max(small[i][k], small[k + 1][j])
                best = max(best, high)
                worst = min(worst, low)
            big[i][j] = best
            small[i][j] = worst
    return [big[0][n - 1], small[0][n - 1]]
