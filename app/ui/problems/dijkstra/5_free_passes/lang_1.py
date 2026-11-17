# 언어 함정: python.shared_rows
import heapq


def solution(n, roads, k):
    graph = [[]] * (n + 1)
    for u, v, toll in roads:
        graph[u].append((v, toll))
        graph[v].append((u, toll))

    INF = float("inf")
    # dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값
    # just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
    dist = [[[INF, INF] for _ in range(k + 1)] for _ in range(n + 1)]
    dist[1][0][0] = 0
    heap = [(0, 1, 0, 0)]
    while heap:
        cost, city, used, just = heapq.heappop(heap)
        if cost > dist[city][used][just]:
            continue
        if city == n:  # 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
            return cost
        for nxt, toll in graph[city]:
            if cost + toll < dist[nxt][used][0]:  # 통행료를 낸다
                dist[nxt][used][0] = cost + toll
                heapq.heappush(heap, (cost + toll, nxt, used, 0))
            if used < k and just == 0 and cost < dist[nxt][used + 1][1]:  # 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                dist[nxt][used + 1][1] = cost
                heapq.heappush(heap, (cost, nxt, used + 1, 1))
    return -1
