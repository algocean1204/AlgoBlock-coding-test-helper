# 틀린 까닭: 꺼진 서버가 파일을 보내지만 않고 받기는 한다고 보아, 꺼진 서버에도 시각을 적고 센다
from collections import deque


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
        neighbors[b].append(a)
    off = set(offline)
    minute = [-1] * (n + 1)
    minute[start] = 0
    queue = deque([start])
    while queue:
        server = queue.popleft()
        for nxt in neighbors[server]:
            if minute[nxt] == -1:
                minute[nxt] = minute[server] + 1
                if nxt not in off:
                    queue.append(nxt)
    latest = max(minute)
    return [latest, minute.count(latest)]
