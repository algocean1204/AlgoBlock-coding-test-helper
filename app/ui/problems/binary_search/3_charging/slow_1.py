# 느린 까닭: 킥보드를 한 대씩, 가장 일찍 끝나는 충전기에 넣어 가며 따라간다(n이 5억이면 5억 번)
import heapq


def solution(n, chargers):
    heap = [(minute, minute) for minute in chargers]
    heapq.heapify(heap)
    finish = 0
    for _ in range(n):
        finish, minute = heapq.heappop(heap)
        heapq.heappush(heap, (finish + minute, minute))
    return finish
