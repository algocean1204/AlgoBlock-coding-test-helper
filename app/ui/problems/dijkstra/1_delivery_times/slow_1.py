# 느린 까닭: 우선순위 큐 없이 매번 모든 마을을 훑어 가장 가까운 마을을 찾는다(마을이 6만 6천 개면 6만 6천 × 6만 6천 번)
def solution(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, time in roads:
        graph[a].append((b, time))
        graph[b].append((a, time))

    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    done = [False] * (n + 1)
    for _ in range(n):
        now = -1
        for town in range(1, n + 1):
            if not done[town] and (now == -1 or dist[town] < dist[now]):
                now = town
        done[now] = True
        for nxt, time in graph[now]:
            if dist[now] + time < dist[nxt]:
                dist[nxt] = dist[now] + time
    return dist[1:]
