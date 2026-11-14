# 틀린 까닭: 큐에 넣을 때 방문 표시를 해서, 나중에 찾은 더 짧은 길로 거리를 고치지 못한다
import heapq


def solution(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a].append((b, time))
        graph[b].append((a, time))

    dist = [0] * (n + 1)
    visited = [False] * (n + 1)
    visited[1] = True
    heap = [(0, 1)]
    while heap:
        d, now = heapq.heappop(heap)
        for nxt, time in graph[now]:
            if not visited[nxt]:
                visited[nxt] = True
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist[1:]
