# 틀린 까닭: 기다린 시간을 수영장에 닿은 시각 - 도착 시각으로 잰다(출발한 시각으로 재야 한다)
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
        if arrive[next_person] <= time and len(sliding) < cap and (last_start is None or time - last_start >= gap):
            sliding.append(time + ride)
            total += time + ride - arrive[next_person]
            last_start = time
            next_person += 1
        time += 1
    return total
