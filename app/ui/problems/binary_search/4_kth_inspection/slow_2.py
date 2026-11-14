# 느린 까닭: 시설마다 다음 점검일을 힙에 넣고, 가장 이른 점검을 하나씩 k번 꺼낸다(k가 400억까지)
import heapq


def solution(schedules, k):
    heap = [(first, i, 1) for i, (first, gap, times) in enumerate(schedules)]
    heapq.heapify(heap)
    while True:
        day, i, done = heapq.heappop(heap)
        k -= 1
        if k == 0:
            return day
        first, gap, times = schedules[i]
        if done < times:
            heapq.heappush(heap, (day + gap, i, done + 1))
