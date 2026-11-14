# 느린 까닭: 점화식은 맞지만 같은 높이의 답을 메모하지 않고 재귀로 매번 다시 구한다(n이 60이면 호출이 10^15번을 넘는다)
def solution(n):
    if n == 0:
        return 1
    total = 0
    for block in (1, 2, 3):
        if n - block >= 0:
            total += solution(n - block)
    return total
