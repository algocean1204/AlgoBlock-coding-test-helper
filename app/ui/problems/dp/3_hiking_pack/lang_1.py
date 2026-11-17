# 언어 함정: python.shared_rows
def solution(items, capacity):
    n = len(items)
    # best[i][w]: 앞의 i개 물건만 보고, 무게 합이 w 이하가 되도록 골랐을 때 쓸모 점수 합의 최댓값
    best = [[0] * (capacity + 1)] * (n + 1)
    for i in range(1, n + 1):
        weight, value = items[i - 1]
        for w in range(capacity + 1):
            best[i][w] = best[i - 1][w]  # i번째 물건을 넣지 않는다
            if weight <= w:  # i번째 물건을 넣는다: 나머지 무게 w - weight는 앞의 물건들로 채운다
                best[i][w] = max(best[i][w], best[i - 1][w - weight] + value)
    return best[n][capacity]
