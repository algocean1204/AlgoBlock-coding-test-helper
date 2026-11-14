# 틀린 까닭: 도로를 뒤집지 않고 시장에서 다익스트라를 돌려, 시장에서 각 마을까지의 시간을 각 마을에서 시장까지의 시간으로 쓴다
import heapq


def dijkstra(graph, n, start, INF=float("inf")):
    dist = [INF] * (n + 1)
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, time in graph[now]:
            if d + time < dist[nxt]:
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist


def solution(n, roads, farms, market):
    small = [[] for _ in range(n + 1)]
    big = [[] for _ in range(n + 1)]
    for u, v, slow, fast in roads:
        small[u].append((v, slow))
        big[u].append((v, fast))
    to_market = dijkstra(big, n, market)
    gather = [0] * (n + 1)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])
    answer = float("inf")
    for m in range(1, n + 1):
        answer = min(answer, gather[m] + to_market[m])
    return answer if answer != float("inf") else -1
