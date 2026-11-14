# 틀린 까닭: 같은 규칙이 여러 번 나올 때 진입 차수는 여러 번 세고 연결은 집합으로 한 번만 적는다(진입 차수가 끝내 0이 되지 않는다)
import heapq


def solution(n, rules):
    after = [set() for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].add(b)
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
    if len(order) < n:
        return []
    return order
