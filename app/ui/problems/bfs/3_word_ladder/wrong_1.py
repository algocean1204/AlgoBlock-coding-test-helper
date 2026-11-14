# 틀린 까닭: 두 낱말의 글자 집합의 차가 한 글자면 한 번에 바꿀 수 있다고 본다(글자의 자리와 겹치는 글자를 무시한다)
from collections import deque


def solution(start, goal, dictionary):
    if goal not in dictionary:
        return -1
    steps = {start: 0}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        if word == goal:
            return steps[word]
        for other in dictionary:
            if other not in steps and len(set(word) - set(other)) == 1:
                steps[other] = steps[word] + 1
                queue.append(other)
    return -1
