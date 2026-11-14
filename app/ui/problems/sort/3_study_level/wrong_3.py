# 틀린 까닭: 'x문제 이상'을 'x문제보다 많이'로 읽는다
def solution(solved):
    ordered = sorted(solved, reverse=True)
    level = 0
    for i in range(len(ordered)):
        if ordered[i] > i + 1:
            level = i + 1
        else:
            break
    return level
