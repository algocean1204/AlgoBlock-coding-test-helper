def solution(n, roads, farms, market):
    # 글의 정의를 그대로: 모든 두 마을 사이의 시간을 플로이드로 구한 뒤, 모이는 마을마다 시각을 따져 본다
    INF = float("inf")
    slow_time = [[INF] * (n + 1) for _ in range(n + 1)]
    fast_time = [[INF] * (n + 1) for _ in range(n + 1)]
    for town in range(1, n + 1):
        slow_time[town][town] = 0
        fast_time[town][town] = 0
    for u, v, slow, fast in roads:
        slow_time[u][v] = min(slow_time[u][v], slow)
        fast_time[u][v] = min(fast_time[u][v], fast)
    for table in (slow_time, fast_time):
        for k in range(1, n + 1):
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    if table[i][k] + table[k][j] < table[i][j]:
                        table[i][j] = table[i][k] + table[k][j]
    best = INF
    for m in range(1, n + 1):
        last = max(slow_time[farm][m] for farm in farms)  # 가장 늦게 도착한 작은 트럭을 기다린다
        best = min(best, last + fast_time[m][market])
    return -1 if best == INF else best
