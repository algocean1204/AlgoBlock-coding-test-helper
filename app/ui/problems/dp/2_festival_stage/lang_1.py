# 언어 함정: python.recursion_limit @ "pay의 길이(축제 기간)는 1 이상 100,000 이하"
def solution(pay):
    n = len(pay)
    if n == 1:
        return pay[0]
    best = [0] * n  # best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
    best[0] = pay[0]
    best[1] = max(pay[0], pay[1])
    def fill(i):  # best[i]를 채우기 전에 best[i - 1]까지 먼저 채운다
        if i < 2:
            return
        fill(i - 1)
        rest = best[i - 1]  # i번째 날은 쉰다
        perform = best[i - 2] + pay[i]  # i번째 날 공연한다: 바로 앞날은 쉬었어야 한다
        best[i] = max(rest, perform)

    fill(n - 1)
    return best[n - 1]
