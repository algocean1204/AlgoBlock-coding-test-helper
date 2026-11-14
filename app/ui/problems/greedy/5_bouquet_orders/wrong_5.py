# 틀린 까닭: 다 만든 시각이 찾으러 오는 시각과 같아도 늦은 것으로 본다(같거나 이르면 지킨 것이다)
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
        while total >= pickup[i] and can_drop:
            total -= -heapq.heappop(can_drop)
            count -= 1
        if total >= pickup[i]:
            return [-1, -1]
    return [count, total]
