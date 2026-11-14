def solution(n, tracks, queries):
    answer = []
    for k, a, b in queries:
        # 열린 역(1~k번)과 양 끝이 열린 선로만으로, 줄어드는 것이 없을 때까지 거리를 고친다(벨만-포드)
        usable = [(x, y, minutes) for x, y, minutes in tracks if x <= k and y <= k]
        dist = {station: None for station in range(1, k + 1)}
        dist[a] = 0
        changed = True
        while changed:
            changed = False
            for x, y, minutes in usable:
                for start, end in ((x, y), (y, x)):
                    if dist[start] is not None and (dist[end] is None or dist[start] + minutes < dist[end]):
                        dist[end] = dist[start] + minutes
                        changed = True
        answer.append(-1 if dist[b] is None else dist[b])
    return answer
