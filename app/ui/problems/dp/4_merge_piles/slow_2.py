# 느린 까닭: 이웃한 두 더미를 합치는 순서를 모두 해 본다(더미가 n개면 (n-1)!가지에 가깝다)
def solution(piles):
    best = [float('inf')]

    def merge_all(current, spent):
        if len(current) == 1:
            best[0] = min(best[0], spent)
            return
        for k in range(len(current) - 1):
            merged = current[k] + current[k + 1]
            merge_all(current[:k] + [merged] + current[k + 2:], spent + merged)

    merge_all(list(piles), 0)
    return best[0]
