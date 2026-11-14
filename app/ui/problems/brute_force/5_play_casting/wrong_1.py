# 틀린 까닭: 함께 설 수 없는 관계를 한쪽 방향(a → b)으로만 적어, 번호가 작은 단원을 나중에 정할 때는 막지 못한다
def solution(members, roles, auditions, rivals):
    n = members
    scores = [[0] * roles for _ in range(n)]
    for member, role, score in auditions:
        scores[member][role] = score
    rivals_of = [[] for _ in range(n)]
    for a, b in rivals:
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
            if used[person] or scores[person][index] == 0:
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
