def solution(n, chargers):
    # 충전기마다 몇 대를 맡길지 모두 따져 본다. x대를 맡긴 충전기는 x × (그 충전기 시간)분에 끝난다.
    # best[j]: 지금까지 본 충전기들에 j대를 나눠 맡겼을 때 모두 끝나는 시간의 최솟값
    never = n * max(chargers) + 1
    best = [0] + [never] * n
    for minute in chargers:
        merged = [never] * (n + 1)
        for j in range(n + 1):
            for x in range(j + 1):
                merged[j] = min(merged[j], max(best[j - x], x * minute))
        best = merged
    return best[n]
