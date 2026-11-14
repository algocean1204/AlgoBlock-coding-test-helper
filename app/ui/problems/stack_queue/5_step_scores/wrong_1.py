# 틀린 까닭: 도착 돌에 닿으면 바로 가고, 아니면 닿는 돌 가운데 점수가 가장 큰 돌로 뛴다(지금 좋아 보이는 돌이 끝까지 좋은 길이라는 보장이 없다)
def solution(scores, jump):
    n = len(scores)
    i = 0
    total = scores[0]
    while i < n - 1:
        if i + jump >= n - 1:
            total += scores[n - 1]
            break
        pick = i + 1
        for j in range(i + 1, i + jump + 1):
            if scores[j] > scores[pick]:
                pick = j
        total += scores[pick]
        i = pick
    return total
