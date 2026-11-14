def solution(scores, jump):
    n = len(scores)
    # reach[i]: i번 돌까지 가는 모든 길 가운데 가장 큰 점수(아직 모르면 None)
    reach = [None] * n
    reach[0] = scores[0]
    # 앞의 돌부터 차례로, 그 돌에서 뛸 수 있는 모든 돌로 한 번씩 뛰어 본다
    for i in range(n):
        for step in range(1, jump + 1):
            j = i + step
            if j >= n:
                break
            score = reach[i] + scores[j]
            if reach[j] is None or score > reach[j]:
                reach[j] = score
    return reach[n - 1]
