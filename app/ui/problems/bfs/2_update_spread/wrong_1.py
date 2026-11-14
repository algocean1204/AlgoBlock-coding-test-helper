# 틀린 까닭: DFS로 처음 들른 깊이를 받는 시각으로 쓴다(고리가 있으면 먼 쪽으로 먼저 돌아 들어가 시각이 커진다)
import sys

sys.setrecursionlimit(200_000)


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
        neighbors[b].append(a)
    off = set(offline)
    minute = [-1] * (n + 1)

    def dfs(server, depth):
        minute[server] = depth
        for nxt in neighbors[server]:
            if minute[nxt] == -1 and nxt not in off:
                dfs(nxt, depth + 1)

    dfs(start, 0)
    latest = max(minute)
    return [latest, minute.count(latest)]
