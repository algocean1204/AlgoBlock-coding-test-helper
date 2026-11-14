# 틀린 까닭: 찾으러 오는 시각 순으로 보며 늦는 주문은 그냥 건너뛴다(앞서 받은 긴 주문을 되무르고 짧은 주문을 받는 편이 나을 때를 놓친다)
import heapq


def solution(pickup, minutes, booked):
    must = set(booked)
    order = sorted(range(len(pickup)), key=lambda i: pickup[i])
    can_drop = []
    count = 0
    total = 0
    for i in order:
        if i not in must:
            if total + minutes[i] <= pickup[i]:  # 늦지 않을 때만 받는다
                total += minutes[i]
                count += 1
                heapq.heappush(can_drop, -minutes[i])
            continue
        count += 1
        total += minutes[i]
        while total > pickup[i] and can_drop:
            total -= -heapq.heappop(can_drop)
            count -= 1
        if total > pickup[i]:
            return [-1, -1]
    return [count, total]
