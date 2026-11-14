# 느린 까닭: 싼 길부터 보지만, 길마다 지금까지 포장한 길을 따라 a에서 b로 갈 수 있는지 처음부터 탐색한다(길 10만 개 × 마을 5만 개)
def solution(n, roads):
    paved_roads = [[] for _ in range(n + 1)]
    total = 0
    paved = 0
    for a, b, cost in sorted(roads, key=lambda road: road[2]):
        seen = [False] * (n + 1)
        seen[a] = True
        stack = [a]
        while stack:
            town = stack.pop()
            for other in paved_roads[town]:
                if not seen[other]:
                    seen[other] = True
                    stack.append(other)
        if seen[b]:
            continue
        paved_roads[a].append(b)
        paved_roads[b].append(a)
        total += cost
        paved += 1
    if paved < n - 1:
        return -1
    return total
