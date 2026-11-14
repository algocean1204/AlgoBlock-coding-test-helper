# 틀린 까닭: 같은 무게를 없애지 않고 늘어놓아 같은 무게를 여러 번 센다
def solution(rows, apples, k):
    weights_of = [[] for _ in range(rows + 1)]
    for row, weight in apples:
        weights_of[row].append(weight)
    answer = []
    for row in range(1, rows + 1):
        kinds = sorted(weights_of[row], reverse=True)
        answer.append(kinds[k - 1] if k <= len(kinds) else -1)
    return answer
