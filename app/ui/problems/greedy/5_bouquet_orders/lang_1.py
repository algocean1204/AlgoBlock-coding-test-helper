# 언어 함정: python.min_heap
import heapq


def solution(pickup, minutes, booked):
    must = set(booked)  # 꼭 받아야 하는 주문 번호
    order = sorted(range(len(pickup)), key=lambda i: pickup[i])  # 찾으러 오는 시각이 이른 주문부터
    can_drop = []  # 되무를 수 있는 받은 주문의 만드는 시간. heapq는 가장 작은 값을 꺼내므로 가장 긴 것을 꺼내려고 음수로 넣는다
    count = 0  # 받은 주문 수
    total = 0  # 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각
    for i in order:
        count += 1
        total += minutes[i]
        if i not in must:
            heapq.heappush(can_drop, minutes[i])
        while total > pickup[i] and can_drop:  # 늦는다: 되무를 수 있는 것 가운데 가장 오래 걸리는 것부터 되무른다
            longest = heapq.heappop(can_drop)
            total -= longest
            count -= 1
        if total > pickup[i]:  # 되무를 것이 없는데도 늦는다: 꼭 받아야 하는 주문끼리도 지킬 수 없다
            return [-1, -1]
    return [count, total]
