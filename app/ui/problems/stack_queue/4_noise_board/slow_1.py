# 느린 까닭: 기록마다 창 안의 기록을 거꾸로 모두 다시 훑는다(창에 기록이 많으면 n × n / 2번 본다)
def solution(logs, window):
    answer = []
    for i in range(len(logs)):
        time = logs[i][0]
        best = 0
        j = i
        while j >= 0 and logs[j][0] > time - window:
            best = max(best, logs[j][1])
            j -= 1
        answer.append(best)
    return answer
