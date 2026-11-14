# 틀린 까닭: 1차원 표를 무게가 작은 쪽부터 채워, 방금 넣은 물건을 같은 차례에 또 넣는다(같은 물건을 여러 번 넣는다)
def solution(items, capacity):
    best = [0] * (capacity + 1)  # best[w]: 무게 합이 w 이하일 때의 최댓값
    for weight, value in items:
        for w in range(weight, capacity + 1):
            best[w] = max(best[w], best[w - weight] + value)
    return best[capacity]
