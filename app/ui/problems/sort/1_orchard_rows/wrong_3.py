# 틀린 까닭: '번째'를 0부터 센 위치로 그대로 써서 k+1번째 무게를 꺼낸다
def solution(rows, apples, k):
    weights_of = [[] for _ in range(rows + 1)]
    for row, weight in apples:
        weights_of[row].append(weight)
    answer = []
    for row in range(1, rows + 1):
        kinds = sorted(set(weights_of[row]), reverse=True)
        answer.append(kinds[k] if k < len(kinds) else -1)
    return answer
