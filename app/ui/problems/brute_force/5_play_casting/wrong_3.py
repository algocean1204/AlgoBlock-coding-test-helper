# 틀린 까닭: 기억할 상태를 '몇 번 배역부터인가'만으로 잡아, 누구를 썼는지가 다른 상태의 값을 잘못 다시 쓴다
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
        if index in memo:
            return memo[index]
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
        memo[index] = result
        return result

    return best(0)
