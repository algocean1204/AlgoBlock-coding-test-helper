# 틀린 까닭: 진료가 끝난 바로 그 시각에 도착한 동물을 후보에 넣지 않는다(도착 시각이 그 시각 이하이면 후보다)
import heapq


def solution(patients):
    n = len(patients)
    arrivals = sorted((arrive, duration, grade, i) for i, (arrive, duration, grade) in enumerate(patients))
    waiting = []
    time = 0
    next_arrival = 0
    total = 0
    for _ in range(n):
        if not waiting and arrivals[next_arrival][0] >= time:
            time = arrivals[next_arrival][0]
            while next_arrival < n and arrivals[next_arrival][0] <= time:
                arrive, duration, grade, i = arrivals[next_arrival]
                heapq.heappush(waiting, (-grade, duration, i, arrive))
                next_arrival += 1
        else:
            while next_arrival < n and arrivals[next_arrival][0] < time:
                arrive, duration, grade, i = arrivals[next_arrival]
                heapq.heappush(waiting, (-grade, duration, i, arrive))
                next_arrival += 1
        _, duration, i, arrive = heapq.heappop(waiting)
        total += time - arrive
        time += duration
    return total
