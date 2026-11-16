# 언어 함정: python.str_to_int @ "공백 하나씩으로 구분한 문자열"
import heapq


def solution(routes, start, goal):
    graph = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, minutes))

    INF = float("inf")
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:  # 이미 더 빠른 시간으로 확정된 선착장
            continue
        if now == goal:  # 도착점은 큐에서 꺼낼 때 확정된다
            return d
        for nxt, minutes in graph.get(now, []):
            if d + minutes < dist.get(nxt, INF):
                dist[nxt] = d + minutes
                heapq.heappush(heap, (dist[nxt], nxt))
    return -1
