# 틀린 까닭: 표의 뜻을 'i번째 날에 반드시 공연할 때의 최댓값'으로 잡고 마지막 칸만 돌려준다(마지막 날을 쉬는 편이 나을 때를 놓친다)
def solution(pay):
    n = len(pay)
    must = [0] * n  # must[i]: i번째 날에 공연할 때 i번째 날까지의 최댓값
    for i in range(n):
        before = 0
        if i >= 2:
            before = max(before, must[i - 2])
        if i >= 3:
            before = max(before, must[i - 3])
        must[i] = before + pay[i]
    return must[n - 1]
