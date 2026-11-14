# 틀린 까닭: 통행권을 k장 모두 쓴 상태의 값만 답으로 본다(통행권은 남겨도 된다)
import heapq


def solution(n, roads, k):
    graph = [[] for _ in range(n + 1)]
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    dist = [[[INF, INF] for _ in range(k + 1)] for _ in range(n + 1)]
    dist[1][0][0] = 0
    heap = [(0, 1, 0, 0)]
    while heap:
        cost, city, used, just = heapq.heappop(heap)
        if cost > dist[city][used][just]:
            continue
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt][used][0]:
                dist[nxt][used][0] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used, 0))
            if used < k and just == 0 and cost < dist[nxt][used + 1][1]:
                dist[nxt][used + 1][1] = cost
                heapq.heappush(heap, (cost, nxt, used + 1, 1))
    answer = min(dist[n][k])
    return answer if answer != INF else -1
