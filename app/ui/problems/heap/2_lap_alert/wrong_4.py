# 틀린 까닭: k위 안에 든 새 기록을 넣기만 하고 밀려난 기록을 꺼내지 않는다(힙이 k개를 넘어 꼭대기가 k위의 경계가 아니다)
import heapq


def solution(records, k):
    fastest = []
    alerts = 0
    for record in records:
        minutes, seconds = record.split(":")
        time = int(minutes) * 60 + int(seconds)
        if len(fastest) < k or time < -fastest[0]:
            alerts += 1
            heapq.heappush(fastest, -time)
    return alerts
