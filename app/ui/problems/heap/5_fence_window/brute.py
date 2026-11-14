def solution(heights, w):
    # 시작 위치마다 판자 w개를 잘라 내고, 맞출 높이로 그 안의 높이를 모두 대 본다(가장 작은 비용은 어느 판자의 높이에서 나온다)
    costs = []
    for start in range(len(heights) - w + 1):
        chosen = heights[start:start + w]
        best = None
        for target in chosen:
            cost = sum(abs(height - target) for height in chosen)
            if best is None or cost < best:
                best = cost
        costs.append(best)
    return costs
