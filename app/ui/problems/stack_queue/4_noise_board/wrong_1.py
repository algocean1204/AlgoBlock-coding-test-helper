# 틀린 까닭: 최근 window초가 아니라 최근 window개의 기록으로 창을 잡는다
from collections import deque


def solution(logs, window):
    answer = []
    candidates = deque()  # (번호, level)
    for i, (time, level) in enumerate(logs):
        while candidates and candidates[-1][1] <= level:
            candidates.pop()
        candidates.append((i, level))
        while candidates[0][0] <= i - window:
            candidates.popleft()
        answer.append(candidates[0][1])
    return answer
