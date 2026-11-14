def solution(piles):
    # 이웃한 두 더미를 합치는 모든 순서를 그대로 해 보고, 걸린 시간 합의 최솟값을 고른다
    if len(piles) == 1:
        return 0
    best = None
    for k in range(len(piles) - 1):
        merged = piles[k] + piles[k + 1]
        rest = piles[:k] + [merged] + piles[k + 2:]
        total = merged + solution(rest)
        if best is None or total < best:
            best = total
    return best
