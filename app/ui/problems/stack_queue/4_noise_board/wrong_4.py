# 틀린 까닭: 창을 벗어난 기록을 덱 앞에서 한 번만 뺀다(while이 아니라 if라서 한꺼번에 여러 개가 벗어나면 오래된 값이 남는다)
from collections import deque


def solution(logs, window):
    answer = []
    candidates = deque()
    for time, level in logs:
        while candidates and candidates[-1][1] <= level:
            candidates.pop()
        candidates.append((time, level))
        if candidates[0][0] <= time - window:
            candidates.popleft()
        answer.append(candidates[0][1])
    return answer
