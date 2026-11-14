# 느린 까닭: 우선순위 큐 없이, 확정하지 않은 상태 (도시, 쓴 장수, 바로 앞에 썼는가)를 매번 모두 훑어 가장 싼 것을 고른다(상태가 20만 개면 20만 번 × 20만 개)
def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = {(city, used, just): INF for city in range(1, n + 1) for used in range(k + 1) for just in range(2)}
    dist[(1, 0, 0)] = 0
    done = set()
    while True:
        state = None
        for key, value in dist.items():
            if key not in done and value != INF and (state is None or value < dist[state]):
                state = key
        if state is None:
            return -1
        city, used, just = state
        cost = dist[state]
        if city == n:
            return cost
        done.add(state)
        for nxt, toll in graph[city]:
            if cost + toll < dist[(nxt, used, 0)]:
                dist[(nxt, used, 0)] = cost + toll
            if used < k and just == 0 and cost < dist[(nxt, used + 1, 1)]:
                dist[(nxt, used + 1, 1)] = cost
