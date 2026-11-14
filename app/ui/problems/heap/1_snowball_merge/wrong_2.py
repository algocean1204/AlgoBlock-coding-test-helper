# 틀린 까닭: 합쳐 만든 눈덩이를 힙에 다시 넣지 않는다(가벼운 것끼리 둘씩 짝만 짓는다)
import heapq


def solution(snowballs):
    heap = list(snowballs)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        total += merged
    return total
