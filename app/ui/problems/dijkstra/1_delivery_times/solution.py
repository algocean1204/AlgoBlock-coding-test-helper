import heapq


def solution(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a].append((b, time))
        graph[b].append((a, time))

    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    heap = [(0, 1)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:  # 이미 더 짧은 시간으로 확정된 마을
            continue
        for nxt, time in graph[now]:
            if d + time < dist[nxt]:
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist[1:]
