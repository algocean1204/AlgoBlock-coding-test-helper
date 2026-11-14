# 느린 까닭: 구간마다 높이를 정렬해 가운데를 찾고 비용을 모두 다시 더한다(구간 4만 개 × 판자 6만 개)
def solution(heights, w):
    costs = []
    for start in range(len(heights) - w + 1):
        chosen = sorted(heights[start:start + w])
        middle = chosen[(w - 1) // 2]
        costs.append(sum(abs(height - middle) for height in chosen))
    return costs
