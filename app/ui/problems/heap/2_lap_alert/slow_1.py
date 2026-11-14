# 느린 까닭: 기록이 들어올 때마다 앞선 기록을 모두 훑어 순위를 센다(10만 개면 10만 × 10만 번에 가깝다)
def solution(records, k):
    times = []
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        ahead = 0
        for earlier in times:
            if earlier <= time:
                ahead += 1
        if ahead < k:
            alerts += 1
        times.append(time)
    return alerts
