# 틀린 까닭: 이웃 조건을 잊고, 힙에서 가장 작은 두 더미를 꺼내 아무 데서나 합친다(이웃하지 않은 더미는 바로 합칠 수 없다)
import heapq


def solution(piles):
    heap = list(piles)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        total += merged
        heapq.heappush(heap, merged)
    return total
