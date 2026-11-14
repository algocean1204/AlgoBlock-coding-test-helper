# 틀린 까닭: 기록이 k개 차기 전에 들어온 기록에는 알림을 세지 않는다(그때는 언제나 k위 안이다)
import heapq


def solution(records, k):
    fastest = []
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        if len(fastest) < k:
            heapq.heappush(fastest, -time)
        elif time < -fastest[0]:
            alerts += 1
            heapq.heappop(fastest)
            heapq.heappush(fastest, -time)
    return alerts
