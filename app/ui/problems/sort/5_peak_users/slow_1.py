# 느린 까닭: 사건 시각 사이 칸마다 인원을 두고, 사용자마다 자기가 걸친 칸을 하나하나 +1 한다(사용자 수 × 칸 수)
def solution(logs):
    times = sorted(set(time for log in logs for time in log))
    where = {}
    for k in range(len(times)):
        where[times[k]] = k
    people = [0] * (len(times) - 1)  # people[k]: times[k]초 ~ times[k+1]-1초의 인원
    for login, logout in logs:
        for k in range(where[login], where[logout]):
            people[k] += 1
    most = max(people)
    seconds = 0
    for k in range(len(people)):
        if people[k] == most:
            seconds += times[k + 1] - times[k]
    return [most, seconds]
