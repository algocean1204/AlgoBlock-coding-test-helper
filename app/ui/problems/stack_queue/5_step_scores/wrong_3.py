# 틀린 까닭: 창을 한 칸 좁게 잡아 바로 앞 jump개가 아니라 jump - 1개만 본다(jump칸 떨어진 돌을 일찍 뺀다)
from collections import deque


def solution(scores, jump):
    n = len(scores)
    best = [0] * n
    best[0] = scores[0]
    window = deque([0])
    for i in range(1, n):
        while len(window) > 1 and window[0] <= i - jump:
            window.popleft()
        best[i] = scores[i] + best[window[0]]
        while window and best[window[-1]] <= best[i]:
            window.pop()
        window.append(i)
    return best[n - 1]
