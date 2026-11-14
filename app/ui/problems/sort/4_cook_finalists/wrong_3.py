# 틀린 까닭: 모양 점수가 같아도 진 것으로 본다('높은'을 '같거나 높은'으로 읽는다)
def solution(taste, look):
    people = sorted(zip(taste, look), key=lambda person: (-person[0], person[1]))
    best_look = -1
    count = 0
    for _, my_look in people:
        if best_look < my_look:
            count += 1
        best_look = max(best_look, my_look)
    return count
