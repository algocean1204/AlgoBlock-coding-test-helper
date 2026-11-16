# 언어 함정: python.shared_rows
def solution(n, tracks, queries):
    INF = float("inf")
    dist = [[INF] * (n + 1)] * (n + 1)
    for station in range(1, n + 1):
        dist[station][station] = 0
    for a, b, minutes in tracks:
        if minutes < dist[a][b]:  # 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
            dist[a][b] = minutes
            dist[b][a] = minutes

    asked = [[] for _ in range(n + 1)]  # asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
    for index, (k, a, b) in enumerate(queries):
        asked[k].append(index)

    answer = [0] * len(queries)
    for k in range(1, n + 1):
        # 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
        # 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
        for index in asked[k]:
            _, a, b = queries[index]
            answer[index] = dist[a][b] if dist[a][b] != INF else -1
    return answer
