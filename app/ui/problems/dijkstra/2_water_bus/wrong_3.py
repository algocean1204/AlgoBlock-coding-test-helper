# 틀린 까닭: 도착점을 큐에 넣는 순간 답으로 돌려준다(나중에 더 빠른 길이 나올 수 있다)
import heapq


def solution(routes, start, goal):
    graph = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, int(minutes)))

    INF = float("inf")
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, minutes in graph.get(now, []):
            if d + minutes < dist.get(nxt, INF):
                if nxt == goal:
                    return d + minutes
                dist[nxt] = d + minutes
                heapq.heappush(heap, (dist[nxt], nxt))
    return -1
