# 언어 함정: python.min_heap @ "위급도가 가장 큰 동물"
import heapq


def solution(patients):
    n = len(patients)
    arrivals = sorted((arrive, duration, grade, i) for i, (arrive, duration, grade) in enumerate(patients))  # 도착 시각 순
    waiting = []  # 도착한 동물: (-위급도, 진료 시간, 번호, 도착 시각). 부호를 뒤집어 위급도가 큰 것이 먼저 나오게 한다
    time = 0
    next_arrival = 0  # arrivals에서 아직 힙에 넣지 않은 첫 자리
    total = 0
    for _ in range(n):
        if not waiting and arrivals[next_arrival][0] > time:
            time = arrivals[next_arrival][0]  # 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
        while next_arrival < n and arrivals[next_arrival][0] <= time:
            arrive, duration, grade, i = arrivals[next_arrival]
            heapq.heappush(waiting, (grade, duration, i, arrive))
            next_arrival += 1
        _, duration, i, arrive = heapq.heappop(waiting)
        total += time - arrive
        time += duration
    return total
