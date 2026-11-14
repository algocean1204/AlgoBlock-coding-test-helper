from collections import deque


def solution(arrive, ride, gap, cap):
    sliding = deque()  # 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞
    next_person = 0    # 줄의 맨 앞 사람 번호
    last_start = None  # 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 None)
    total = 0
    time = 0
    while next_person < len(arrive):
        while sliding and sliding[0] == time:  # 먼저 벗어난다
            sliding.popleft()
        arrived = arrive[next_person] <= time
        room = len(sliding) < cap
        gap_passed = last_start is None or time - last_start >= gap
        if arrived and room and gap_passed:  # 그다음 맨 앞 사람 한 명이 출발한다
            sliding.append(time + ride)
            total += time - arrive[next_person]
            last_start = time
            next_person += 1
        time += 1
    return total
