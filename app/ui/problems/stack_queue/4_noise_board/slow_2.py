# 느린 까닭: 가장 큰 값과 그 시각만 들고 다니다가 그 값이 창 밖으로 나갈 때만 창 안을 다시 훑는다(소음이 줄어들기만 하면 매번 다시 훑는다)
def solution(logs, window):
    answer = []
    start = 0           # 창 안에서 가장 오래된 기록의 번호
    best_time = -1
    best = 0
    for i in range(len(logs)):
        time, level = logs[i]
        while logs[start][0] <= time - window:
            start += 1
        if level >= best:
            best, best_time = level, time
        elif best_time <= time - window:
            best = 0
            for j in range(start, i + 1):
                if logs[j][1] >= best:
                    best, best_time = logs[j][1], logs[j][0]
        answer.append(best)
    return answer
