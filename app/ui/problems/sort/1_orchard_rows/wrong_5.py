# 틀린 까닭: 적은 무게가 k개보다 적을 때 -1 대신 그 줄에서 가장 가벼운 무게를 답한다(사과가 없는 줄만 -1)
def solution(rows, apples, k):
    weights_of = [[] for _ in range(rows + 1)]
    for row, weight in apples:
        weights_of[row].append(weight)
    answer = []
    for row in range(1, rows + 1):
        kinds = sorted(set(weights_of[row]), reverse=True)
        if not kinds:
            answer.append(-1)
        else:
            answer.append(kinds[min(k, len(kinds)) - 1])
    return answer
