def solution(logs):
    # 사건을 정렬해 훑지 않는다. 기록에 나온 시각들 사이(a초 ~ b-1초)는 아무도 들어오거나 나가지 않으므로
    # 그 동안의 인원은 a초의 인원과 같다. a초의 인원은 정의(login <= a < logout) 그대로 모든 기록을 보고 센다.
    times = sorted(set(time for log in logs for time in log))
    pieces = []
    for k in range(len(times) - 1):
        a, b = times[k], times[k + 1]
        people = 0
        for login, logout in logs:
            if login <= a < logout:
                people += 1
        pieces.append((people, b - a))
    most = max(people for people, _ in pieces)
    seconds = 0
    for people, length in pieces:
        if people == most:
            seconds += length
    return [most, seconds]
