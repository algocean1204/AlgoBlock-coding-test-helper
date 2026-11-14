# 느린 까닭: 구간마다 나올 수 있는 값을 모두 모아 둔다(메모는 하지만 값이 수천 가지라 두 묶음의 값을 짝짓는 데 시간이 모자란다)
def solution(values, signs):
    n = len(values)
    every = [[None] * n for _ in range(n)]
    for i in range(n):
        every[i][i] = {values[i]}
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            out = set()
            for k in range(i, j):
                for left in every[i][k]:
                    for right in every[k + 1][j]:
                        if signs[k] == '+':
                            out.add(left + right)
                        elif signs[k] == '-':
                            out.add(left - right)
                        else:
                            out.add(max(left, right))
            every[i][j] = out
    return [max(every[0][n - 1]), min(every[0][n - 1])]
