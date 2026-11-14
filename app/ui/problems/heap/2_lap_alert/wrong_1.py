# 틀린 까닭: 경계(k위)와 시간이 같은 새 기록도 k위 안으로 센다(같으면 먼저 들어온 기록이 앞선다)
import heapq


def solution(records, k):
    fastest = []
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        if len(fastest) < k:
            alerts += 1
            heapq.heappush(fastest, -time)
        elif time <= -fastest[0]:
            alerts += 1
            heapq.heappop(fastest)
            heapq.heappush(fastest, -time)
    return alerts
