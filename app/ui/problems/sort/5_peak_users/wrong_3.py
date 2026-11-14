# 틀린 까닭: 최댓값이 새로 바뀌었는데 앞서 모아 둔 시간을 지우지 않고 계속 더한다
def solution(logs):
    events = []
    for login, logout in logs:
        events.append((login, 1))
        events.append((logout, -1))
    events.sort()
    inside = most = seconds = 0
    for i in range(len(events) - 1):
        time, change = events[i]
        inside += change
        length = events[i + 1][0] - time
        if inside > most:
            most = inside
            seconds += length
        elif inside == most:
            seconds += length
    return [most, seconds]
