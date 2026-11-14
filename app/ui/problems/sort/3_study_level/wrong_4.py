# 틀린 까닭: 정렬하지 않은 채 앞에서부터 같은 방법으로 훑는다(앞에서 i+1명이 가장 많이 푼 회원들이 아니다)
def solution(solved):
    level = 0
    for i in range(len(solved)):
        if solved[i] >= i + 1:
            level = i + 1
        else:
            break
    return level
