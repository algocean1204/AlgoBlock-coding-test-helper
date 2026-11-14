# 틀린 까닭: 무한대를 10억(int(1e9))으로 둔다(시간 합이 10억을 넘는 마을은 닿지 못한 것처럼 남는다)
import heapq

INF = 10**9


def dijkstra(graph, n, start):
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
        big_back[v].append((u, fast))
    to_market = dijkstra(big_back, n, market)
    gather = [0] * (n + 1)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])
    answer = INF
    for m in range(1, n + 1):
        if gather[m] < INF and to_market[m] < INF:
            answer = min(answer, gather[m] + to_market[m])
    return answer if answer != INF else -1
