from itertools import product


def solution(items, capacity):
    # 물건마다 넣을지(1) 말지(0)를 모두 정해 보고, 무게 합이 capacity 이하인 것 가운데 쓸모 합의 최댓값
    n = len(items)
    answer = 0
    for plan in product((0, 1), repeat=n):
        weight = sum(items[i][0] for i in range(n) if plan[i] == 1)
        value = sum(items[i][1] for i in range(n) if plan[i] == 1)
        if weight <= capacity:
            answer = max(answer, value)
    return answer
