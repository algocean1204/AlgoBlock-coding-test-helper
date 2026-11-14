# 틀린 까닭: heapq에 만드는 시간을 그대로 넣어 가장 짧은 주문을 되무른다(heapq는 가장 작은 값을 꺼낸다)
import heapq


def solution(pickup, minutes, booked):
    must = set(booked)
    order = sorted(range(len(pickup)), key=lambda i: pickup[i])
    can_drop = []
    count = 0
    total = 0
    for i in order:
        count += 1
        total += minutes[i]
        if i not in must:
            heapq.heappush(can_drop, minutes[i])
        while total > pickup[i] and can_drop:
            total -= heapq.heappop(can_drop)
            count -= 1
        if total > pickup[i]:
            return [-1, -1]
    return [count, total]
