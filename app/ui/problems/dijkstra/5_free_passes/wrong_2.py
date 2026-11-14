# 틀린 까닭: 거리 표를 도시마다 하나만 두어, 통행료는 조금 더 냈어도 통행권을 더 많이 남기고 온 경로를 버린다
import heapq


def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    heap = [(0, 1, 0, 0)]
    while heap:
        cost, city, used, just = heapq.heappop(heap)
        if cost > dist[city]:
            continue
        if city == n:
            return cost
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt]:
                dist[nxt] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used, 0))
            if used < k and just == 0 and cost < dist[nxt]:
                dist[nxt] = cost
                heapq.heappush(heap, (cost, nxt, used + 1, 1))
    return -1
