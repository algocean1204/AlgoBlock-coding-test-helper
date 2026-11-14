from collections import deque


def solution(scores, jump):
    n = len(scores)
    best = [0] * n  # best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값
    best[0] = scores[0]
    window = deque([0])  # 바로 앞 jump개 돌의 번호. 앞에서 뒤로 갈수록 best가 작다
    for i in range(1, n):
        # i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
        while window[0] < i - jump:
            window.popleft()
        best[i] = scores[i] + best[window[0]]
        # best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
        while window and best[window[-1]] <= best[i]:
            window.pop()
        window.append(i)
    return best[n - 1]
