# 틀린 까닭: 출발하는 0번 돌의 점수를 더하지 않고 0에서 시작한다
from collections import deque


def solution(scores, jump):
    n = len(scores)
    best = [0] * n
    best[0] = 0
    window = deque([0])
    for i in range(1, n):
        while window[0] < i - jump:
            window.popleft()
        best[i] = scores[i] + best[window[0]]
        while window and best[window[-1]] <= best[i]:
            window.pop()
        window.append(i)
    return best[n - 1]
