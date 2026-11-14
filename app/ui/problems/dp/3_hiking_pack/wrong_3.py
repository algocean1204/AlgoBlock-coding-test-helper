# 틀린 까닭: 표의 뜻을 '무게 합이 정확히 w'로 잡고(만들 수 없는 무게는 -1) best[capacity]만 돌려준다(꽉 채울 수 없을 때 틀린다)
def solution(items, capacity):
    best = [-1] * (capacity + 1)  # best[w]: 무게 합이 정확히 w일 때의 최댓값, 만들 수 없으면 -1
    best[0] = 0
    for weight, value in items:
        for w in range(capacity, weight - 1, -1):
            if best[w - weight] >= 0:
                best[w] = max(best[w], best[w - weight] + value)
    return max(best[capacity], 0)
