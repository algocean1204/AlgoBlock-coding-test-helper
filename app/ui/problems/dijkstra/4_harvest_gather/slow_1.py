# 느린 까닭: 모이는 마을마다 그 마을에서 다익스트라를 새로 돌려 시장까지 큰 트럭의 시간을 구한다(마을이 2만 곳이면 다익스트라 2만 번)
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
    gather = [0] * (n + 1)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])
    answer = float("inf")
    for m in range(1, n + 1):
        if gather[m] != float("inf"):
            answer = min(answer, gather[m] + dijkstra(big, n, m)[market])
    return answer if answer != float("inf") else -1
