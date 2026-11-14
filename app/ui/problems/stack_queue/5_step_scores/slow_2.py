# 느린 까닭: 범위의 가장 큰 최고 점수와 그 돌 번호만 들고 다니다가, 그 돌이 범위를 벗어날 때만 범위를 다시 훑는다(최고 점수가 줄어들기만 하면 매번 jump개를 다시 훑는다)
def solution(scores, jump):
    n = len(scores)
    best = [0] * n
    best[0] = scores[0]
    top, top_i = best[0], 0
    for i in range(1, n):
        if top_i < i - jump:
            top_i = i - jump
            for k in range(i - jump, i):
                if best[k] >= best[top_i]:
                    top_i = k
            top = best[top_i]
        best[i] = scores[i] + top
        if best[i] >= top:
            top, top_i = best[i], i
    return best[n - 1]
