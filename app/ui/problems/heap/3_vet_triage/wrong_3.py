# 틀린 까닭: 위급도가 같을 때 진료 시간이 아니라 도착 시각으로 고른다(먼저 온 동물을 먼저 보는 습관대로)
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
            heapq.heappush(waiting, (-grade, arrive, i, duration))
            next_arrival += 1
        _, arrive, i, duration = heapq.heappop(waiting)
        total += time - arrive
        time += duration
    return total
