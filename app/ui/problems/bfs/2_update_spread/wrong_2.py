# 틀린 까닭: 케이블을 a에서 b로 가는 한 방향으로만 넣는다(케이블은 양쪽 방향이다)
from collections import deque


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
    off = set(offline)
    minute = [-1] * (n + 1)
    minute[start] = 0
    queue = deque([start])
    while queue:
        server = queue.popleft()
        for nxt in neighbors[server]:
            if minute[nxt] == -1 and nxt not in off:
                minute[nxt] = minute[server] + 1
                queue.append(nxt)
    latest = max(minute)
    return [latest, minute.count(latest)]
