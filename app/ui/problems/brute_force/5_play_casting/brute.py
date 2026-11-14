from itertools import permutations


def solution(members, roles, auditions, rivals):
    # 글의 정의를 그대로: 배역마다 서로 다른 단원을 정하는 모든 방법을 만들어 조건을 확인한다
    score_of = {(member, role): score for member, role, score in auditions}
    answer = -1
    for cast in permutations(range(members), roles):  # cast[j] = j번 배역을 맡은 단원
        if any((person, j) not in score_of for j, person in enumerate(cast)):  # 오디션을 보지 않은 배역
            continue
        if any(a in cast and b in cast for a, b in rivals):
            continue
        answer = max(answer, sum(score_of[(person, j)] for j, person in enumerate(cast)))
    return answer
