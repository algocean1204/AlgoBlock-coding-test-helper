def solution(n, roads, k):
    # 상태 (도시, 쓴 통행권 수, 바로 앞 도로에 통행권을 썼는가)마다 낸 통행료의 최솟값을 두고,
    # 모든 도로로 값을 줄이는 일을 더 줄어드는 것이 없을 때까지 되풀이한다(벨만-포드. 큐를 쓰지 않는다)
    INF = float("inf")
    best = {(1, 0, 0): 0}
    changed = True
    while changed:
        changed = False
        for (city, used, just), cost in list(best.items()):
            for u, v, toll in roads:
                for a, b in ((u, v), (v, u)):
                    if a != city:
                        continue
                    moves = [((b, used, 0), cost + toll)]
                    if used < k and just == 0:
                        moves.append(((b, used + 1, 1), cost))
                    for state, value in moves:
                        if value < best.get(state, INF):
                            best[state] = value
                            changed = True
    found = [cost for (city, _, _), cost in best.items() if city == n]
    return min(found) if found else -1
