# 틀린 까닭: 같은 두 역 사이 선로가 여러 개일 때 나중에 나온 선로로 덮어쓴다(더 짧은 선로를 남겨야 한다)
def solution(n, tracks, queries):
    INF = float("inf")
    dist = [[INF] * (n + 1) for _ in range(n + 1)]
    for station in range(1, n + 1):
        dist[station][station] = 0
    for a, b, minutes in tracks:
        dist[a][b] = minutes
        dist[b][a] = minutes
    asked = [[] for _ in range(n + 1)]
    for index, (k, a, b) in enumerate(queries):
        asked[k].append(index)
    answer = [0] * len(queries)
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] != INF else -1
    return answer
