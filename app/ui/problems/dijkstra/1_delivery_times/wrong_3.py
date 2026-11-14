# 틀린 까닭: 어느 방향으로든 지날 수 있는 길을 a → b 한쪽으로만 넣는다
import heapq


def solution(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a].append((b, time))

    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    heap = [(0, 1)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, time in graph[now]:
            if d + time < dist[nxt]:
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist[1:]
