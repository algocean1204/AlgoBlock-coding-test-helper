# 틀린 까닭: 최댓값이었던 때가 여러 번 떨어져 있어도 가장 긴 한 번만 센다
def solution(logs):
    events = []
    for login, logout in logs:
        events.append((login, 1))
        events.append((logout, -1))
    events.sort()
    inside = most = 0
    best_run = run = 0  # 가장 긴 한 번, 지금 이어지는 한 번
    for i in range(len(events) - 1):
        time, change = events[i]
        inside += change
        length = events[i + 1][0] - time
        if length == 0:
            continue
        if inside > most:
            most, run, best_run = inside, length, length
        elif inside == most:
            run += length
            best_run = max(best_run, run)
        else:
            run = 0
    return [most, best_run]
