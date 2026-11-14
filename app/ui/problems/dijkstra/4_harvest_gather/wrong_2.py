# 틀린 까닭: 한 방향 도로를 양쪽 방향으로 다닐 수 있다고 보고 그래프에 두 방향 모두 넣는다
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
    big_back = [[] for _ in range(n + 1)]
    for u, v, slow, fast in roads:
        small[u].append((v, slow))
        small[v].append((u, slow))
        big_back[v].append((u, fast))
        big_back[u].append((v, fast))
    to_market = dijkstra(big_back, n, market)
    gather = [0] * (n + 1)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])
    answer = float("inf")
    for m in range(1, n + 1):
        answer = min(answer, gather[m] + to_market[m])
    return answer if answer != float("inf") else -1
