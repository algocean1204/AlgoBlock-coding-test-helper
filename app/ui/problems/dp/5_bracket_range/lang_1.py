# 언어 함정: python.shared_rows
def solution(values, signs):
    n = len(values)
    big = [[0] * n] * n    # big[i][j]: values[i] ~ values[j]를 괄호로 묶어 만들 수 있는 가장 큰 값
    small = [[0] * n for _ in range(n)]  # small[i][j]: 같은 구간의 가장 작은 값
    for i in range(n):
        big[i][i] = values[i]
        small[i][i] = values[i]
    for length in range(2, n + 1):  # 짧은 구간부터 채운다
        for i in range(n - length + 1):
            j = i + length - 1
            best = float('-inf')
            worst = float('inf')
            for k in range(i, j):  # signs[k]를 맨 마지막에 계산한다: [i, k]와 [k + 1, j]로 나뉜다
                if signs[k] == '+':
                    high = big[i][k] + big[k + 1][j]
                    low = small[i][k] + small[k + 1][j]
                elif signs[k] == '-':
                    high = big[i][k] - small[k + 1][j]  # 빼는 쪽은 가장 작을 때 결과가 가장 크다
                    low = small[i][k] - big[k + 1][j]
                else:  # '^': 두 값 가운데 큰 값
                    high = max(big[i][k], big[k + 1][j])
                    low = max(small[i][k], small[k + 1][j])  # 큰 값을 작게 하려면 양쪽을 모두 작게 한다
                best = max(best, high)
                worst = min(worst, low)
            big[i][j] = best
            small[i][j] = worst
    return [big[0][n - 1], small[0][n - 1]]
