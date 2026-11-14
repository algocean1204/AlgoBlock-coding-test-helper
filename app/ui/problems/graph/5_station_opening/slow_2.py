# 느린 까닭: 질문에 나온 k마다 1~k번 역만으로 플로이드를 처음부터 다시 돌린다(k가 300가지면 1³ + 2³ + … + 300³ ≈ 20억 번)
def solution(n, tracks, queries):
    INF = float("inf")
    tables = {}
    answer = []
    for k, a, b in queries:
        if k not in tables:
            dist = [[INF] * (k + 1) for _ in range(k + 1)]
            for station in range(1, k + 1):
                dist[station][station] = 0
            for x, y, minutes in tracks:
                if x <= k and y <= k and minutes < dist[x][y]:
                    dist[x][y] = minutes
                    dist[y][x] = minutes
            for m in range(1, k + 1):
                for i in range(1, k + 1):
                    for j in range(1, k + 1):
                        if dist[i][m] + dist[m][j] < dist[i][j]:
                            dist[i][j] = dist[i][m] + dist[m][j]
            tables[k] = dist
        shortest = tables[k][a][b]
        answer.append(shortest if shortest != INF else -1)
    return answer
