# 틀린 까닭: 조건을 만족한 마지막 자리의 값(푼 문제 수)을 답으로 돌려준다(답은 사람 수 쪽이다)
def solution(solved):
    ordered = sorted(solved, reverse=True)
    level = 0
    for i in range(len(ordered)):
        if ordered[i] >= i + 1:
            level = ordered[i]
        else:
            break
    return level
