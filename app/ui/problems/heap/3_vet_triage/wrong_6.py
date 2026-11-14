# 틀린 까닭: 쉬다가 다음 동물의 도착 시각으로 건너뛸 때 그 동물 하나만 넣고 바로 고른다(같은 시각에 도착한 다른 동물을 빠뜨린다)
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
            arrive, duration, grade, i = arrivals[next_arrival]
            time = arrive
            heapq.heappush(waiting, (-grade, duration, i, arrive))
            next_arrival += 1
        else:
            while next_arrival < n and arrivals[next_arrival][0] <= time:
                arrive, duration, grade, i = arrivals[next_arrival]
                heapq.heappush(waiting, (-grade, duration, i, arrive))
                next_arrival += 1
        _, duration, i, arrive = heapq.heappop(waiting)
        total += time - arrive
        time += duration
    return total
