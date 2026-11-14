# 틀린 까닭: 두 도시 사이 도로를 딕셔너리에 덮어써서, 같은 두 도시를 잇는 도로가 여러 개면 마지막에 적힌 도로만 남는다
import heapq


def solution(n, roads, k):
    graph = [{} for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u][v] = toll
        graph[v][u] = toll

    INF = float("inf")
    dist = [[[INF, INF] for _ in range(k + 1)] for _ in range(n + 1)]
    dist[1][0][0] = 0
    heap = [(0, 1, 0, 0)]
    while heap:
        cost, city, used, just = heapq.heappop(heap)
        if cost > dist[city][used][just]:
            continue
        if city == n:
            return cost
        for nxt, toll in graph[city].items():
            if cost + toll < dist[nxt][used][0]:
                dist[nxt][used][0] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used, 0))
            if used < k and just == 0 and cost < dist[nxt][used + 1][1]:
                dist[nxt][used + 1][1] = cost
                heapq.heappush(heap, (cost, nxt, used + 1, 1))
    return -1
