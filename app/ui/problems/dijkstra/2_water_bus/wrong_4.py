# 틀린 까닭: 노선 수가 가장 적은 길을 BFS로 찾아 그 길의 시간을 답으로 한다(노선을 더 많이 타도 더 빠를 수 있다)
from collections import deque


def solution(routes, start, goal):
    graph = {}
    for route in routes:
        departure, arrival, minutes = route.split()
        graph.setdefault(departure, []).append((arrival, int(minutes)))

    time = {start: 0}
    queue = deque([start])
    while queue:
        now = queue.popleft()
        if now == goal:
            return time[now]
        for nxt, minutes in graph.get(now, []):
            if nxt not in time:
                time[nxt] = time[now] + minutes
                queue.append(nxt)
    return -1
