# 틀린 까닭: 맛 점수가 같으면 모양 점수가 높은 사람부터 보아, 같은 맛 점수인 참가자끼리 서로 떨어뜨린다
def solution(taste, look):
    people = sorted(zip(taste, look), key=lambda person: (-person[0], -person[1]))
    best_look = -1
    count = 0
    for _, my_look in people:
        if best_look <= my_look:
            count += 1
        best_look = max(best_look, my_look)
    return count
