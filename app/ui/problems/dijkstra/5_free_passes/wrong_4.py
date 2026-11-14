# 틀린 까닭: 통행권을 연달아 쓸 수 없다는 규칙을 빠뜨려, 이어진 도로에 통행권을 잇달아 쓴다
import heapq


def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = [[INF] * (k + 1) for _ in range(n + 1)]
    dist[1][0] = 0
    heap = [(0, 1, 0)]
    while heap:
        cost, city, used = heapq.heappop(heap)
        if cost > dist[city][used]:
            continue
        if city == n:
            return cost
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt][used]:
                dist[nxt][used] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used))
            if used < k and cost < dist[nxt][used + 1]:
                dist[nxt][used + 1] = cost
                heapq.heappush(heap, (cost, nxt, used + 1))
    return -1
