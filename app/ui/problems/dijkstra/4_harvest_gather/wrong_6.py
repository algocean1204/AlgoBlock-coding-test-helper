# 틀린 까닭: 어느 마을로도 수확물을 시장에 보낼 수 없을 때 -1 대신 0을 돌려준다(닿지 못하는 마을을 건너뛰기만 한다)
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
        big_back[v].append((u, fast))
    to_market = dijkstra(big_back, n, market)
    gather = [0] * (n + 1)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])
    answer = 0
    for m in range(1, n + 1):
        total = gather[m] + to_market[m]
        if total != float("inf") and (answer == 0 or total < answer):
            answer = total
    return answer
