# 틀린 까닭: 둘째 칸의 시작값을 pay[1]로 둔다(첫날만 공연하는 편이 나을 때를 놓친다)
def solution(pay):
    n = len(pay)
    if n == 1:
        return pay[0]
    best = [0] * n
    best[0] = pay[0]
    best[1] = pay[1]
    for i in range(2, n):
        best[i] = max(best[i - 1], best[i - 2] + pay[i])
    return best[n - 1]
