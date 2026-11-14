def solution(n, roads):
    # 벨만-포드: 더 줄일 수 있는 길이 없을 때까지 모든 길로 거리를 줄인다
    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[1] = 0
    changed = True
    while changed:
        changed = False
        for a, b, time in roads:
            if dist[a] + time < dist[b]:
                dist[b] = dist[a] + time
                changed = True
            if dist[b] + time < dist[a]:
                dist[a] = dist[b] + time
                changed = True
    return dist[1:]
