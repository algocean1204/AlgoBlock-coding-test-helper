# 틀린 까닭: 같은 시각에 출발할 수 있는지를 그 시각에 벗어날 사람이 벗어나기 전에 확인한다(벗어나기가 먼저여야 한다)
from collections import deque


def solution(arrive, ride, gap, cap):
    sliding = deque()
    next_person = 0
    last_start = None
    total = 0
    time = 0
    while next_person < len(arrive):
        if arrive[next_person] <= time and len(sliding) < cap and (last_start is None or time - last_start >= gap):
            sliding.append(time + ride)
            total += time - arrive[next_person]
            last_start = time
            next_person += 1
        while sliding and sliding[0] <= time:
            sliding.popleft()
        time += 1
    return total
