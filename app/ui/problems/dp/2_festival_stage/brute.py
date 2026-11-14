from itertools import product


def solution(pay):
    # 날마다 공연할지(1) 쉴지(0)를 모두 정해 보고, 연달아 이틀 공연하는 경우를 뺀 나머지 가운데 최댓값
    n = len(pay)
    answer = 0
    for plan in product((0, 1), repeat=n):
        if any(plan[i] == 1 and plan[i + 1] == 1 for i in range(n - 1)):
            continue
        answer = max(answer, sum(pay[i] for i in range(n) if plan[i] == 1))
    return answer
