# 틀린 까닭: 금메달로만 정렬해, 금메달이 같은 반은 입력 순서대로 남는다
def solution(classes, medals):
    order = sorted(range(len(classes)), key=lambda i: -medals[i][0])
    return [classes[i] for i in order]
