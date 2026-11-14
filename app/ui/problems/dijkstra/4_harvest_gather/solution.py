import heapq


def dijkstra(graph, n, start):
    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, now = heapq.heappop(heap)
        if d > dist[now]:
            continue
        for nxt, time in graph[now]:
            if d + time < dist[nxt]:
                dist[nxt] = d + time
                heapq.heappush(heap, (dist[nxt], nxt))
    return dist


def solution(n, roads, farms, market):
    small = [[] for _ in range(n + 1)]  # 작은 트럭: u → v, slow분
    big_back = [[] for _ in range(n + 1)]  # 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
    for u, v, slow, fast in roads:
        small[u].append((v, slow))
        big_back[v].append((u, fast))

    # 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
    to_market = dijkstra(big_back, n, market)

    gather = [0] * (n + 1)  # gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
    for farm in farms:
        arrive = dijkstra(small, n, farm)
        for m in range(1, n + 1):
            gather[m] = max(gather[m], arrive[m])

    answer = float("inf")
    for m in range(1, n + 1):  # 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
        answer = min(answer, gather[m] + to_market[m])
    return answer if answer != float("inf") else -1
