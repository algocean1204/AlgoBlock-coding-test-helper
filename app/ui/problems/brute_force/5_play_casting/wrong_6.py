# 틀린 까닭: 오디션을 보지 않은 배역도 맡을 수 있다고 보고(점수 0으로) 맡긴다
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
    memo = {}

    def best(index):
        if index == roles:
            return 0
        state = (index, tuple(used))
        if state in memo:
            return memo[state]
        result = -1
        for person in range(n):
            if used[person]:
                continue
            if any(used[other] for other in rivals_of[person]):
                continue
            used[person] = True
            rest = best(index + 1)
            used[person] = False
            if rest != -1:
                result = max(result, scores[person][index] + rest)
        memo[state] = result
        return result

    return best(0)
