# 틀린 까닭: 꼭 받아야 하는 주문도 되무를 후보에 넣는다(예약을 되무르고, 예약을 지킬 수 없는 경우를 알아채지 못한다)
import heapq


def solution(pickup, minutes, booked):
    order = sorted(range(len(pickup)), key=lambda i: pickup[i])
    taken = []
    total = 0
    for i in order:
        heapq.heappush(taken, -minutes[i])
        total += minutes[i]
        if total > pickup[i]:
            total -= -heapq.heappop(taken)
    return [len(taken), total]
