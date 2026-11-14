# 틀린 까닭: 사과를 따지 않은 줄을 빠뜨리고 사과가 있는 줄만 답에 담는다
def solution(rows, apples, k):
    weights_of = {}
    for row, weight in apples:
        weights_of.setdefault(row, []).append(weight)
    answer = []
    for row in sorted(weights_of):
        kinds = sorted(set(weights_of[row]), reverse=True)
        answer.append(kinds[k - 1] if k <= len(kinds) else -1)
    return answer
