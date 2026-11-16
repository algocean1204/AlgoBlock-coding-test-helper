# 언어 함정: python.min_heap
import heapq


def solution(records, k):
    fastest = []  # 지금까지 가장 빠른 기록 k개. 부호를 뒤집어 넣어 가장 느린 기록(k위)이 꼭대기에 온다
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        if len(fastest) < k:
            alerts += 1
            heapq.heappush(fastest, time)
        elif time < fastest[0]:  # 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
            alerts += 1
            heapq.heappop(fastest)
            heapq.heappush(fastest, time)
    return alerts
