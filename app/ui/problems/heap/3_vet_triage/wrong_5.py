# 틀린 까닭: 기다린 시간을 진료가 끝난 시각 - 도착 시각으로 잰다(시작한 시각으로 재야 한다)
import heapq


def solution(patients):
    n = len(patients)
    arrivals = sorted((arrive, duration, grade, i) for i, (arrive, duration, grade) in enumerate(patients))
    waiting = []
    time = 0
    next_arrival = 0
    total = 0
    for _ in range(n):
        if not waiting and arrivals[next_arrival][0] > time:
            time = arrivals[next_arrival][0]
        while next_arrival < n and arrivals[next_arrival][0] <= time:
            arrive, duration, grade, i = arrivals[next_arrival]
            heapq.heappush(waiting, (-grade, duration, i, arrive))
            next_arrival += 1
        _, duration, i, arrive = heapq.heappop(waiting)
        time += duration
        total += time - arrive
    return total
