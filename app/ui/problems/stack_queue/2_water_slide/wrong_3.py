# 틀린 까닭: 아직 줄에 도착하지 않은 사람도 출발시킨다(도착 시각 전에는 출발할 수 없다)
from collections import deque


def solution(arrive, ride, gap, cap):
    sliding = deque()
    next_person = 0
    last_start = None
    total = 0
    time = 0
    while next_person < len(arrive):
        while sliding and sliding[0] == time:
            sliding.popleft()
        if len(sliding) < cap and (last_start is None or time - last_start >= gap):
            sliding.append(time + ride)
            total += max(0, time - arrive[next_person])
            last_start = time
            next_person += 1
        time += 1
    return total
