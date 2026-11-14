# 틀린 까닭: INF를 int 최댓값(2,147,483,647)으로 두어 INF + INF가 넘쳐 음수가 된다(Java·C++·Go·Rust에서 생기는 일을 32비트 덧셈으로 흉내 냈다)
def solution(n, tracks, queries):
    INF = 2**31 - 1
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
                through = dist[i][k] + dist[k][j]
                if through > INF:  # 32비트 int는 최댓값을 넘으면 음수로 돌아간다
                    through -= 2**32
                if through < dist[i][j]:
                    dist[i][j] = through
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] != INF else -1
    return answer
