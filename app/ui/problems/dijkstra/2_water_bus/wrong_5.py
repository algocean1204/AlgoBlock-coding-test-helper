# 틀린 까닭: 같은 두 선착장 사이 노선 가운데 하나만 남기면서 시간을 글자로 비교한다("10"이 "9"보다 앞선다)
import heapq


def solution(routes, start, goal):
    fastest = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        if (departure, arrival) not in fastest or minutes < fastest[(departure, arrival)]:
            fastest[(departure, arrival)] = minutes
    graph = {}
    for (departure, arrival), minutes in fastest.items():
        graph.setdefault(departure, []).append((arrival, int(minutes)))

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
