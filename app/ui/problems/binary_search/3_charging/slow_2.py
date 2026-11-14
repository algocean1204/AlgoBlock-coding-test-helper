# 느린 까닭: 시간을 1분씩 늘려 가며 n대가 되는지 확인한다(답이 수조 분까지 커진다)
def solution(n, chargers):
    time = 1
    while True:
        done = 0
        for minute in chargers:
            done += time // minute
        if done >= n:
            return time
        time += 1
