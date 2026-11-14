def solution(taste, look):
    people = []
    for i in range(len(taste)):
        people.append((-taste[i], look[i]))
    # 맛 점수가 높은 사람부터 본다. 맛 점수가 같으면 모양 점수가 낮은 사람부터 본다.
    # 같은 맛 점수끼리는 서로 떨어뜨리지 못하므로, 같은 무리에서 모양 점수가 높은 사람이
    # 먼저 지나가 best_look을 올려 두면 안 된다.
    people.sort()

    best_look = -1  # 지금까지 지나간 사람들의 모양 점수 가운데 가장 높은 값
    count = 0
    for _, my_look in people:
        # 앞에 지나간 사람은 나보다 맛 점수가 높거나, 같은 맛 점수에 모양 점수가 나 이하다.
        # 그러니 best_look이 내 모양 점수보다 높으면, 맛도 모양도 나보다 높은 사람이 있다는 뜻이다.
        if best_look <= my_look:
            count += 1
        best_look = max(best_look, my_look)
    return count
