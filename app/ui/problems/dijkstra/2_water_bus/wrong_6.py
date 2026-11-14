# 틀린 까닭: 같은 두 선착장 사이 노선을 합치려고 두 이름을 그대로 이어 붙인 글자를 키로 써서, 다른 쌍이 섞인다("ab"+"c"와 "a"+"bc")
import heapq


def solution(routes, start, goal):
    fastest = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        key = departure + arrival
        if key not in fastest or int(minutes) < fastest[key][2]:
            fastest[key] = (departure, arrival, int(minutes))
    graph = {}
    for departure, arrival, minutes in fastest.values():
        graph.setdefault(departure, []).append((arrival, minutes))

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
