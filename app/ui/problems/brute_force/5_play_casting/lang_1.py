# 언어 함정: python.shared_rows
def solution(members, roles, auditions, rivals):
    n = members  # 단원 수
    scores = [[0] * roles] * n  # scores[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
    for member, role, score in auditions:
        scores[member][role] = score
    rivals_of = [[] for _ in range(n)]  # 함께 무대에 설 수 없는 단원(양쪽에 모두 적는다)
    for a, b in rivals:
        rivals_of[a].append(b)
        rivals_of[b].append(a)

    used = [False] * n
    memo = {}  # (몇 번 배역부터 정할 차례인가, 누구를 썼는가) → 거기서 더 얻을 수 있는 가장 큰 점수

    def best(index):
        """index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1."""
        if index == roles:
            return 0
        state = (index, tuple(used))
        if state in memo:  # 같은 상태에 다시 왔다: 그 뒤는 같으므로 기억한 값을 쓴다
            return memo[state]
        result = -1
        for person in range(n):
            if used[person] or scores[person][index] == 0:
                continue
            if any(used[other] for other in rivals_of[person]):  # 이미 정한 단원과 부딪치면 이 가지는 버린다
                continue
            used[person] = True
            rest = best(index + 1)
            used[person] = False
            if rest != -1:  # 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
                result = max(result, scores[person][index] + rest)
        memo[state] = result
        return result

    return best(0)
