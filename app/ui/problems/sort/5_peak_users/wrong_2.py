# 틀린 까닭: logout초에도 접속해 있다고 본다(끊는 사건을 logout + 1초에 둔다)
def solution(logs):
    events = []
    for login, logout in logs:
        events.append((login, 1))
        events.append((logout + 1, -1))
    events.sort()
    inside = most = seconds = 0
    for i in range(len(events) - 1):
        time, change = events[i]
        inside += change
        length = events[i + 1][0] - time
        if inside > most:
            most, seconds = inside, length
        elif inside == most:
            seconds += length
    return [most, seconds]
