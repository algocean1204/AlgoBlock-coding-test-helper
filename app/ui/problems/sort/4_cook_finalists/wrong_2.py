# 틀린 까닭: 맛 점수로만 정렬해, 같은 맛 점수끼리의 순서를 입력 순서에 맡긴다
def solution(taste, look):
    people = sorted(zip(taste, look), key=lambda person: -person[0])
    best_look = -1
    count = 0
    for _, my_look in people:
        if best_look <= my_look:
            count += 1
        best_look = max(best_look, my_look)
    return count
