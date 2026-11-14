# 느린 까닭: 하나 설치할 때마다 1번부터 모든 패키지를 훑어 설치할 수 있는 가장 작은 번호를 찾는다(10만 개면 10만 × 10만 번)
def solution(n, rules):
    after = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1
    installed = [False] * (n + 1)
    order = []
    for _ in range(n):
        chosen = 0
        for package in range(1, n + 1):
            if not installed[package] and waiting[package] == 0:
                chosen = package
                break
        if chosen == 0:
            return []
        installed[chosen] = True
        order.append(chosen)
        for nxt in after[chosen]:
            waiting[nxt] -= 1
    return order
