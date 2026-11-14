# 틀린 까닭: x를 solved에 들어 있는 값 가운데에서만 찾는다(답은 solved에 없는 값일 수 있다)
def solution(solved):
    ordered = sorted(solved)
    n = len(ordered)
    best = 0
    for i in range(n):
        x = ordered[i]
        if n - i >= x:  # x 이상인 회원은 i번째부터 끝까지
            best = max(best, x)
    return best
