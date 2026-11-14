# 틀린 까닭: 지금까지의 가장 큰 값 하나만 들고 다녀, 창 밖으로 나간 값을 계속 보여 준다
def solution(logs, window):
    answer = []
    best = 0
    for time, level in logs:
        best = max(best, level)
        answer.append(best)
    return answer
