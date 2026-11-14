# 느린 까닭: 구간 점화식은 맞지만 메모하지 않고 재귀로 매번 다시 구한다(더미가 n개면 호출이 약 3^n번)
def solution(piles):
    def cost(i, j):  # i ~ j번째 더미를 한 더미로 만드는 최소 시간
        if i == j:
            return 0
        best = float('inf')
        for k in range(i, j):
            best = min(best, cost(i, k) + cost(k + 1, j))
        return best + sum(piles[i:j + 1])

    return cost(0, len(piles) - 1)
