# 틀린 까닭: 두 마을 사이의 길을 딕셔너리에 덮어써서, 같은 두 마을을 잇는 길이 여러 개면 마지막에 적힌 길만 남는다
import heapq


def solution(n, roads):
    graph = [{} for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a][b] = time
        graph[b][a] = time

    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    heap = [(0, 1)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, time in graph[now].items():
            if d + time < dist[nxt]:
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist[1:]
