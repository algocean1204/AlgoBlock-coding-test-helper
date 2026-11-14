# 틀린 까닭: 구간의 평균 높이(소수점 아래 버림)로 맞춘다(높이 차이의 합은 가운데 높이에서 가장 작다)
def solution(heights, w):
    costs = []
    window_sum = sum(heights[:w])
    for start in range(len(heights) - w + 1):
        if start > 0:
            window_sum += heights[start + w - 1] - heights[start - 1]
        target = window_sum // w
        costs.append(sum(abs(height - target) for height in heights[start:start + w]))
    return costs
