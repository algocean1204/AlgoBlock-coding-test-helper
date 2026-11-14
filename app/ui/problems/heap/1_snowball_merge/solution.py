import heapq


def solution(snowballs):
    heap = list(snowballs)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        lightest = heapq.heappop(heap)
        second = heapq.heappop(heap)
        merged = lightest + second
        total += merged
        heapq.heappush(heap, merged)
    return total
