# 틀린 까닭: 시각표를 아주 큰 값으로 채워 두고 최댓값을 구해, 파일을 받지 못한 서버까지 센다
from collections import deque


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
        neighbors[b].append(a)
    off = set(offline)
    big = 10**9
    minute = [big] * (n + 1)
    minute[start] = 0
    queue = deque([start])
    while queue:
        server = queue.popleft()
        for nxt in neighbors[server]:
            if minute[nxt] == big and nxt not in off:
                minute[nxt] = minute[server] + 1
                queue.append(nxt)
    latest = max(minute[1:])
    return [latest, minute[1:].count(latest)]
