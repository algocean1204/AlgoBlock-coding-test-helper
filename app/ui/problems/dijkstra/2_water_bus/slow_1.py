# 느린 까닭: 우선순위 큐 없이 매번 모든 선착장을 훑어 가장 가까운 곳을 찾는다(선착장이 5만 개면 5만 × 5만 번)
def solution(routes, start, goal):
    graph = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, int(minutes)))
        graph.setdefault(arrival, [])

    INF = float("inf")
    dist = {name: INF for name in graph}
    dist[start] = 0
    done = set()
    while True:
        now = None
        for name in graph:
            if name not in done and (now is None or dist[name] < dist[now]):
                now = name
        if now is None or dist[now] == INF:
            return -1
        if now == goal:
            return dist[now]
        done.add(now)
        for nxt, minutes in graph[now]:
            if dist[now] + minutes < dist[nxt]:
                dist[nxt] = dist[now] + minutes
