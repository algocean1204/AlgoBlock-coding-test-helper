# 틀린 까닭: 정확히 t - window초에 찍힌 기록도 창에 넣는다(창의 왼쪽 끝은 들어가지 않는다)
from collections import deque


def solution(logs, window):
    answer = []
    candidates = deque()
    for time, level in logs:
        while candidates and candidates[-1][1] <= level:
            candidates.pop()
        candidates.append((time, level))
        while candidates[0][0] < time - window:
            candidates.popleft()
        answer.append(candidates[0][1])
    return answer
