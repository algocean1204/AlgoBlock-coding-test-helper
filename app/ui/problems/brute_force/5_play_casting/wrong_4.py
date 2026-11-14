# 틀린 까닭: 더 정할 수 없는 가지를 -1이 아니라 0점으로 돌려, 배역을 다 채우지 못한 배정의 점수까지 답으로 삼는다
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
        result = 0
        for person in range(n):
            if used[person] or scores[person][index] == 0:
                continue
            if any(used[other] for other in rivals_of[person]):
                continue
            used[person] = True
            result = max(result, scores[person][index] + best(index + 1))
            used[person] = False
        memo[state] = result
        return result

    answer = best(0)
    return answer if answer > 0 else -1
