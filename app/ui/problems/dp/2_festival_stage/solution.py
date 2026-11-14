def solution(pay):
    n = len(pay)
    if n == 1:
        return pay[0]
    best = [0] * n  # best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
    best[0] = pay[0]
    best[1] = max(pay[0], pay[1])
    for i in range(2, n):
        rest = best[i - 1]  # i번째 날은 쉰다
        perform = best[i - 2] + pay[i]  # i번째 날 공연한다: 바로 앞날은 쉬었어야 한다
        best[i] = max(rest, perform)
    return best[n - 1]
