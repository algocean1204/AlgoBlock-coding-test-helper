# 틀린 까닭: 바로 앞 도로에 통행권을 썼는지를 큐에만 싣고 거리 표는 (도시, 쓴 장수)로만 두어, 같은 값이면 다음 도로에 통행권을 쓸 수 있는 상태를 버린다
import heapq


def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = [[INF] * (k + 1) for _ in range(n + 1)]
    dist[1][0] = 0
    heap = [(0, 1, 0, 0)]
    while heap:
        cost, city, used, just = heapq.heappop(heap)
        if cost > dist[city][used]:
            continue
        if city == n:
            return cost
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt][used]:
                dist[nxt][used] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used, 0))
            if used < k and just == 0 and cost < dist[nxt][used + 1]:
                dist[nxt][used + 1] = cost
                heapq.heappush(heap, (cost, nxt, used + 1, 1))
    return -1
