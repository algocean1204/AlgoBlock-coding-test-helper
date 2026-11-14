# 틀린 까닭: 꺼낸 개수를 확인하지 않는다(사이클이 있으면 빈 배열이 아니라 일부만 담긴 순서를 돌려준다)
import heapq


def solution(n, rules):
    after = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1
    ready = [package for package in range(1, n + 1) if waiting[package] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        package = heapq.heappop(ready)
        order.append(package)
        for nxt in after[package]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                heapq.heappush(ready, nxt)
    return order
