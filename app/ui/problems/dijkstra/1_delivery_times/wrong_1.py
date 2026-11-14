# 틀린 까닭: BFS처럼 처음 닿은 길로 거리를 정해 버린다(길을 더 많이 지나도 더 빠른 경로를 놓친다)
from collections import deque


def solution(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a].append((b, time))
        graph[b].append((a, time))

    dist = [-1] * (n + 1)
    dist[1] = 0
    queue = deque([1])
    while queue:
        now = queue.popleft()
        for nxt, time in graph[now]:
            if dist[nxt] == -1:
                dist[nxt] = dist[now] + time
                queue.append(nxt)
    return dist[1:]
