# 틀린 까닭: k번째 반복에서 이미 문을 연 역(1~k번)끼리의 거리만 고친다(나중에 열 역까지 가는 거리가 고쳐지지 않아, 그 역이 열린 뒤 그 역을 지나는 길을 놓친다)
def solution(n, tracks, queries):
    INF = float("inf")
    dist = [[INF] * (n + 1) for _ in range(n + 1)]
    for station in range(1, n + 1):
        dist[station][station] = 0
    for a, b, minutes in tracks:
        if minutes < dist[a][b]:
            dist[a][b] = minutes
            dist[b][a] = minutes
    asked = [[] for _ in range(n + 1)]
    for index, (k, a, b) in enumerate(queries):
        asked[k].append(index)
    answer = [0] * len(queries)
    for k in range(1, n + 1):
        for i in range(1, k + 1):
            for j in range(1, k + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] != INF else -1
    return answer
