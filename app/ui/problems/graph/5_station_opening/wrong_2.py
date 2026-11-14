# 틀린 까닭: k번 역을 거쳐 가는 갱신을 하기 전에 k의 질문에 답한다(방금 문을 연 k번 역을 지나는 길을 놓친다)
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
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] != INF else -1
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return answer
