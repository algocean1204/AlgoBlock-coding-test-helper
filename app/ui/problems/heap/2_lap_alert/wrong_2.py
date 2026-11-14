# 틀린 까닭: 부호를 뒤집지 않아 꼭대기가 가장 빠른 기록이다. 경계를 1위로 잘못 보고, 넘칠 때 가장 빠른 기록을 버린다
import heapq


def solution(records, k):
    fastest = []
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        if len(fastest) < k:
            alerts += 1
            heapq.heappush(fastest, time)
        elif time < fastest[0]:
            alerts += 1
            heapq.heappop(fastest)
            heapq.heappush(fastest, time)
    return alerts
