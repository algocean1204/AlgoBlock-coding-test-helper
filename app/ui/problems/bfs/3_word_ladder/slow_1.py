# 느린 까닭: 꺼낸 낱말마다 사전 전체와 한 자리씩 견주어 이웃을 찾는다(낱말이 2만 개면 2만 × 2만 번 견준다)
from collections import deque


def solution(start, goal, dictionary):
    def one_apart(a, b):
        diff = 0
        for i in range(len(a)):
            if a[i] != b[i]:
                diff += 1
        return diff == 1

    steps = {start: 0}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        if word == goal:
            return steps[word]
        for other in dictionary:
            if other not in steps and one_apart(word, other):
                steps[other] = steps[word] + 1
                queue.append(other)
    return -1
