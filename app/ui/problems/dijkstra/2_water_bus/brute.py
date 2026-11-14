def solution(routes, start, goal):
    # 벨만-포드: 더 줄일 수 있는 노선이 없을 때까지 모든 노선으로 시간을 줄인다
    edges = []
    for route in routes:
        departure, arrival, minutes = route.split()
        edges.append((departure, arrival, int(minutes)))
    INF = float("inf")
    dist = {start: 0}
    changed = True
    while changed:
        changed = False
        for departure, arrival, minutes in edges:
            if dist.get(departure, INF) + minutes < dist.get(arrival, INF):
                dist[arrival] = dist[departure] + minutes
                changed = True
    return dist.get(goal, -1)
