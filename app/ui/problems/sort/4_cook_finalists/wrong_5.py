# 틀린 까닭: 맛 점수가 낮은 사람부터 훑어, 나보다 맛 점수가 낮은 사람의 모양 점수와 비교한다(정렬 방향이 반대다)
def solution(taste, look):
    people = sorted(zip(taste, look))
    best_look = -1
    count = 0
    for _, my_look in people:
        if best_look <= my_look:
            count += 1
        best_look = max(best_look, my_look)
    return count
