# 틀린 까닭: 같은 초에 접속과 끊음이 겹치면 접속을 먼저 처리해, 잠깐 부풀어 오른 인원을 최댓값으로 센다
def solution(logs):
    events = []
    for login, logout in logs:
        events.append((login, "in"))
        events.append((logout, "out"))
    events.sort()  # 같은 초면 "in"이 "out"보다 앞에 온다
    inside = most = seconds = 0
    for i in range(len(events) - 1):
        time, kind = events[i]
        inside += 1 if kind == "in" else -1
        length = events[i + 1][0] - time
        if inside > most:
            most, seconds = inside, length
        elif inside == most:
            seconds += length
    return [most, seconds]
