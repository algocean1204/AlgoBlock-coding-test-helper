# 틀린 까닭: 넣을 수 있는지를 weight < w(미만)로 비교해, 물건을 넣어 배낭을 꽉 채우는 경우를 놓친다
def solution(items, capacity):
    n = len(items)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        weight, value = items[i - 1]
        for w in range(capacity + 1):
            best[i][w] = best[i - 1][w]
            if weight < w:
                best[i][w] = max(best[i][w], best[i - 1][w - weight] + value)
    return best[n][capacity]
