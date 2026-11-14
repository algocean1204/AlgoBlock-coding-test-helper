# 느린 까닭: 설치할 수 있는 패키지를 목록에 모아 두고 매번 min으로 가장 작은 것을 찾아 지운다(목록이 길면 한 번에 수만 번, 모두 합쳐 수십억 번)
def solution(n, rules):
    after = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1
    ready = [package for package in range(1, n + 1) if waiting[package] == 0]
    order = []
    while ready:
        package = min(ready)
        ready.remove(package)
        order.append(package)
        for nxt in after[package]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
    if len(order) < n:
        return []
    return order
