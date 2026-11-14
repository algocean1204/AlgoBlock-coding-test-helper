# 틀린 까닭: 배역마다 지금 맡을 수 있는 단원 가운데 점수가 가장 높은 단원을 바로 고른다(앞에서 욕심내면 뒤가 막히거나 손해다)
def solution(members, roles, auditions, rivals):
    n = members
    scores = [[0] * roles for _ in range(n)]
    for member, role, score in auditions:
        scores[member][role] = score
    rivals_of = [[] for _ in range(n)]
    for a, b in rivals:
        rivals_of[a].append(b)
        rivals_of[b].append(a)
    used = [False] * n
    total = 0
    for index in range(roles):
        pick = -1
        for person in range(n):
            if used[person] or scores[person][index] == 0:
                continue
            if any(used[other] for other in rivals_of[person]):
                continue
            if pick == -1 or scores[person][index] > scores[pick][index]:
                pick = person
        if pick == -1:
            return -1
        used[pick] = True
        total += scores[pick][index]
    return total
