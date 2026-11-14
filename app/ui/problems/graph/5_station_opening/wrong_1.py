# 틀린 까닭: 모든 역이 열린 거리표 하나로 모든 질문에 답한다(아직 문을 열지 않은 역을 지나는 길까지 쓴다)
def solution(n, tracks, queries):
    INF = float("inf")
    dist = [[INF] * (n + 1) for _ in range(n + 1)]
    for station in range(1, n + 1):
        dist[station][station] = 0
    for a, b, minutes in tracks:
        if minutes < dist[a][b]:
            dist[a][b] = minutes
            dist[b][a] = minutes
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return [dist[a][b] if dist[a][b] != INF else -1 for k, a, b in queries]
