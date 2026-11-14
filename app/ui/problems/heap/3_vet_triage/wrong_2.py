# 틀린 까닭: 위급도를 부호를 뒤집지 않고 최소 힙에 넣어 덜 위급한 동물부터 고른다
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
            heapq.heappush(waiting, (grade, duration, i, arrive))
            next_arrival += 1
        _, duration, i, arrive = heapq.heappop(waiting)
        total += time - arrive
        time += duration
    return total
