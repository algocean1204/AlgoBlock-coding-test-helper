# 느린 까닭: 돌마다 바로 앞 jump개 돌의 최고 점수를 다시 훑어 가장 큰 값을 찾는다(n × jump번 본다)
def solution(scores, jump):
    n = len(scores)
    best = [0] * n
    best[0] = scores[0]
    for i in range(1, n):
        best[i] = scores[i] + max(best[max(0, i - jump):i])
    return best[n - 1]
