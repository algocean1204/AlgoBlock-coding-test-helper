# 틀린 까닭: 바꾼 결과가 goal이면 dictionary에 있는지 보지 않고 도착한 것으로 본다(goal도 dictionary에 있어야 한다)
from collections import deque


def solution(start, goal, dictionary):
    words = set(dictionary)
    letters = "abcdefghijklmnopqrstuvwxyz"
    steps = {start: 0}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        for i in range(len(word)):
            for ch in letters:
                if ch == word[i]:
                    continue
                candidate = word[:i] + ch + word[i + 1:]
                if candidate == goal:
                    return steps[word] + 1
                if candidate in words and candidate not in steps:
                    steps[candidate] = steps[word] + 1
                    queue.append(candidate)
    return -1
