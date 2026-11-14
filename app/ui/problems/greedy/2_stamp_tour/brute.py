def solution(kinds, minutes, time):
    # 부스를 고르는 모든 경우를 본다: 걸린 시간의 합이 time 이하인 것 가운데 서로 다른 모양의 수가 가장 큰 것
    n = len(kinds)
    best = 0
    for mask in range(1 << n):
        total = 0
        shapes = set()
        for i in range(n):
            if mask >> i & 1:
                total += minutes[i]
                shapes.add(kinds[i])
        if total <= time:
            best = max(best, len(shapes))
    return best
