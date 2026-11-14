# 틀린 까닭: 큐에서 꺼낼 때 방문 표시를 하고 넣을 때마다 시각을 덮어써서, 아직 꺼내지 않은 서버의 시각이 같은 층 서버를 거친 더 큰 값으로 바뀐다
from collections import deque


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
        neighbors[b].append(a)
    off = set(offline)
    visited = [False] * (n + 1)
    minute = [-1] * (n + 1)
    minute[start] = 0
    queue = deque([start])
    while queue:
        server = queue.popleft()
        if visited[server]:
            continue
        visited[server] = True
        for nxt in neighbors[server]:
            if not visited[nxt] and nxt not in off:
                minute[nxt] = minute[server] + 1
                queue.append(nxt)
    latest = max(minute)
    return [latest, minute.count(latest)]
