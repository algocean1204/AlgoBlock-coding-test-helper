def solution(n, roads):
    # 1번 마을에서 시작해, 이어진 마을과 아직 이어지지 않은 마을을 잇는 길 가운데 가장 싼 것을 하나씩 더한다(프림)
    joined = {1}
    total = 0
    while len(joined) < n:
        best = None
        for a, b, cost in roads:
            if (a in joined) != (b in joined) and (best is None or cost < best[2]):
                best = (a, b, cost)
        if best is None:
            return -1
        joined.add(best[0])
        joined.add(best[1])
        total += best[2]
    return total
