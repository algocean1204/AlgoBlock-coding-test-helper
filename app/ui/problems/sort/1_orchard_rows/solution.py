def solution(rows, apples, k):
    weights_of = [[] for _ in range(rows + 1)]  # weights_of[줄 번호] = 그 줄의 사과 무게들(0번 칸은 쓰지 않는다)
    for row, weight in apples:
        weights_of[row].append(weight)

    answer = []
    for row in range(1, rows + 1):
        kinds = sorted(set(weights_of[row]), reverse=True)  # 같은 무게는 한 번만, 무거운 것부터
        if k <= len(kinds):
            answer.append(kinds[k - 1])  # k번째 무게는 위치 k-1
        else:
            answer.append(-1)  # 적은 무게가 k개보다 적다(사과가 없는 줄 포함)
    return answer
