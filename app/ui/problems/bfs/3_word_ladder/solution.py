from collections import deque


def solution(start, goal, dictionary):
    words = set(dictionary)
    if goal not in words:
        return -1
    letters = "abcdefghijklmnopqrstuvwxyz"

    # steps[w]: start에서 w를 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
    steps = {start: 0}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        if word == goal:
            return steps[word]
        for i in range(len(word)):
            for ch in letters:
                if ch == word[i]:
                    continue
                candidate = word[:i] + ch + word[i + 1:]  # 한 자리만 바꾼 이웃 후보를 직접 만든다
                if candidate in words and candidate not in steps:
                    steps[candidate] = steps[word] + 1
                    queue.append(candidate)
    return -1
