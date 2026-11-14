# 틀린 까닭: 갈 수 없을 때 -1로 바꾸지 않고 처음에 넣어 둔 큰 값을 그대로 돌려준다
import heapq


def solution(routes, start, goal):
    INF = 1_000_000_000
    graph = {}
    dist = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, int(minutes)))
        dist[departure] = INF
        dist[arrival] = INF

    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, minutes in graph.get(now, []):
            if d + minutes < dist[nxt]:
                dist[nxt] = d + minutes
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist[goal]
