# 틀린 까닭: 한 방향 노선을 양쪽 방향으로 넣어, 거꾸로 탈 수 없는 노선을 지름길로 쓴다
import heapq


def solution(routes, start, goal):
    graph = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, int(minutes)))
        graph.setdefault(arrival, []).append((departure, int(minutes)))

    INF = float("inf")
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        if now == goal:
            return d
        for nxt, minutes in graph.get(now, []):
            if d + minutes < dist.get(nxt, INF):
                dist[nxt] = d + minutes
                heapq.heappush(heap, (dist[nxt], nxt))
    return -1
