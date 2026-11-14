# 느린 까닭: DFS로 내려가며 더 짧은 시각을 찾을 때마다 그 서버부터 다시 내려간다(같은 서버를 몇 번이고 다시 고친다)
import sys

sys.setrecursionlimit(200_000)


def solution(n, cables, start, offline):
    neighbors = [[] for _ in range(n + 1)]
    for a, b in cables:
        neighbors[a].append(b)
        neighbors[b].append(a)
    off = set(offline)
    big = n + 1
    minute = [big] * (n + 1)
    minute[start] = 0

    def dfs(server):
        for nxt in neighbors[server]:
            if nxt not in off and minute[server] + 1 < minute[nxt]:
                minute[nxt] = minute[server] + 1
                dfs(nxt)

    dfs(start)
    got = [m for m in minute[1:] if m < big]
    return [max(got), got.count(max(got))]
