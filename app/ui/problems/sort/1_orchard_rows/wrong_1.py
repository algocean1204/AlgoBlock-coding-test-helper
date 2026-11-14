# 틀린 까닭: 가벼운 것부터 늘어놓아 k번째로 가벼운 무게를 구한다
def solution(rows, apples, k):
    weights_of = [[] for _ in range(rows + 1)]
    for row, weight in apples:
        weights_of[row].append(weight)
    answer = []
    for row in range(1, rows + 1):
        kinds = sorted(set(weights_of[row]))
        answer.append(kinds[k - 1] if k <= len(kinds) else -1)
    return answer
