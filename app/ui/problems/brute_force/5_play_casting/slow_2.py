# 느린 까닭: 배역을 맡을 단원 묶음을 먼저 고른 뒤, 그 묶음으로 배역을 나누는 순서를 모두 바꿔 본다(묶음마다 최대 9! = 362,880번)
from itertools import combinations, permutations


def solution(members, roles, auditions, rivals):
    n = members
    scores = [[0] * roles for _ in range(n)]
    for member, role, score in auditions:
        scores[member][role] = score
    answer = -1
    for team in combinations(range(n), roles):
        members = set(team)
        if any(a in members and b in members for a, b in rivals):
            continue
        for cast in permutations(team):
            total = 0
            for j, person in enumerate(cast):
                if scores[person][j] == 0:
                    break
                total += scores[person][j]
            else:
                answer = max(answer, total)
    return answer
