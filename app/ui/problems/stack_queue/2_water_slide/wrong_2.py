# 틀린 까닭: 앞사람이 출발한 뒤 gap초가 '지나야'를 gap초보다 '더 지나야'로 본다(t + gap초에 출발할 수 있다)
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
        if arrive[next_person] <= time and len(sliding) < cap and (last_start is None or time - last_start > gap):
            sliding.append(time + ride)
            total += time - arrive[next_person]
            last_start = time
            next_person += 1
        time += 1
    return total
