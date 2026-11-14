# 틀린 까닭: '갈 수 없음'을 뜻하는 INF를 100,000으로 잡는다(실제 가장 짧은 시간은 299 × 1,000 = 299,000분까지 간다)
def solution(n, tracks, queries):
    INF = 100_000
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
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] < INF else -1
    return answer
