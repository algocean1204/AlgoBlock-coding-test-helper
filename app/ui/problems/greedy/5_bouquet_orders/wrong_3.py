# 틀린 까닭: 늦으면 하나만 되무른다(꼭 받아야 하는 긴 주문이 들어오면 여럿을 되물러야 할 수 있다)
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
            heapq.heappush(can_drop, -minutes[i])
        if total > pickup[i] and can_drop:  # while이 아니라 if: 한 번만 되무른다
            total -= -heapq.heappop(can_drop)
            count -= 1
        if total > pickup[i]:
            return [-1, -1]
    return [count, total]
