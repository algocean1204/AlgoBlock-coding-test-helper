# 느린 까닭: 이어진 마을에서 가장 싸게 닿는 마을을 고를 때마다 모든 마을을 훑는다(프림을 힙 없이: 5만 × 5만 번)
def solution(n, roads):
    INF = float("inf")
    linked = [[] for _ in range(n + 1)]
    for a, b, cost in roads:
        linked[a].append((b, cost))
        linked[b].append((a, cost))
    best = [INF] * (n + 1)
    joined = [False] * (n + 1)
    best[1] = 0
    total = 0
    for _ in range(n):
        town = 0
        for candidate in range(1, n + 1):
            if not joined[candidate] and (town == 0 or best[candidate] < best[town]):
                town = candidate
        if best[town] == INF:
            return -1
        joined[town] = True
        total += best[town]
        for other, cost in linked[town]:
            if not joined[other] and cost < best[other]:
                best[other] = cost
    return total
