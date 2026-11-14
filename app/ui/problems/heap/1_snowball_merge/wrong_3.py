# 틀린 까닭: 눈덩이가 둘 남았을 때 반복을 멈춰 마지막 합치기를 빠뜨린다
import heapq


def solution(snowballs):
    heap = list(snowballs)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 2:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        total += merged
        heapq.heappush(heap, merged)
    return total
