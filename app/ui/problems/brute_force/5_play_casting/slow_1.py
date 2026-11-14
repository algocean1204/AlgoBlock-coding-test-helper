# 느린 까닭: 상태를 기억하지 않고 모든 배정을 끝까지 해 본다(단원 14명에 배역 9개면 14 × 13 × … × 6, 7억 가지가 넘는다)
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

    def best(index):
        if index == roles:
            return 0
        result = -1
        for person in range(n):
            if used[person] or scores[person][index] == 0:
                continue
            if any(used[other] for other in rivals_of[person]):
                continue
            used[person] = True
            rest = best(index + 1)
            used[person] = False
            if rest != -1:
                result = max(result, scores[person][index] + rest)
        return result

    return best(0)
