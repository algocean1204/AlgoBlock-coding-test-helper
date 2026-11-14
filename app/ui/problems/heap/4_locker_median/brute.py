def solution(houses):
    # 거리 합은 꺾인 직선들의 합이라 가장 작은 값은 어느 집의 위치에서 나온다. 그 위치들을 모두 대 본다
    total = 0
    for day in range(1, len(houses) + 1):
        built = houses[:day]
        best = None
        for spot in built:
            distance = sum(abs(house - spot) for house in built)
            if best is None or distance < best:
                best = distance
        total += best
    return total
