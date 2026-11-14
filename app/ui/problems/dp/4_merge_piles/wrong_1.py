# 틀린 까닭: 매번 합이 가장 작은 이웃한 두 더미부터 합친다(지금 가장 싼 선택이 끝까지 가장 싸지는 않다)
def solution(piles):
    piles = list(piles)
    total = 0
    while len(piles) > 1:
        k = 0
        for i in range(len(piles) - 1):
            if piles[i] + piles[i + 1] < piles[k] + piles[k + 1]:
                k = i
        merged = piles[k] + piles[k + 1]
        total += merged
        piles[k:k + 2] = [merged]
    return total
