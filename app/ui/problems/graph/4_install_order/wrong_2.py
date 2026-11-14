# 틀린 까닭: 보통 큐로 먼저 들어온 것부터 꺼낸다(나중에 설치할 수 있게 된 작은 번호가 먼저 들어와 있던 큰 번호 뒤로 밀린다)
from collections import deque


def solution(n, rules):
    after = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1
    ready = deque(package for package in range(1, n + 1) if waiting[package] == 0)
    order = []
    while ready:
        package = ready.popleft()
        order.append(package)
        for nxt in sorted(after[package]):
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
    if len(order) < n:
        return []
    return order
