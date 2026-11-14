# 틀린 까닭: 통행료 합이 가장 적은 길을 먼저 찾고, 그 길에서 비싼 도로부터 이웃하지 않게 k개까지 통행권을 쓴다(통행권을 쓰면 더 싸지는 다른 길을 놓친다)
import heapq


def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = [INF] * (n + 1)
    came_from = [None] * (n + 1)  # (앞 도시, 그 도로의 통행료)
    dist[1] = 0
    heap = [(0, 1)]
    while heap:
        cost, city = heapq.heappop(heap)
        if cost > dist[city]:
            continue
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt]:
                dist[nxt] = cost + toll
                came_from[nxt] = (city, toll)
                heapq.heappush(heap, (dist[nxt], nxt))
    if dist[n] == INF:
        return -1

    tolls = []
    city = n
    while city != 1:
        city, toll = came_from[city]
        tolls.append(toll)
    free = [False] * len(tolls)
    left = k
    for i in sorted(range(len(tolls)), key=lambda i: -tolls[i]):
        if left > 0 and not (i > 0 and free[i - 1]) and not (i + 1 < len(tolls) and free[i + 1]):
            free[i] = True
            left -= 1
    return sum(toll for toll, is_free in zip(tolls, free) if not is_free)
