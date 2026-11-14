# 느린 까닭: 늦을 때마다 받은 주문 전체에서 max로 가장 긴 것을 찾고 remove로 지운다(받은 수 × 늦은 횟수)
def solution(pickup, minutes, booked):
    must = set(booked)
    order = sorted(range(len(pickup)), key=lambda i: pickup[i])
    can_drop = []  # 되무를 수 있는 받은 주문의 만드는 시간(그냥 목록)
    count = 0
    total = 0
    for i in order:
        count += 1
        total += minutes[i]
        if i not in must:
            can_drop.append(minutes[i])
        while total > pickup[i] and can_drop:
            longest = max(can_drop)
            can_drop.remove(longest)
            total -= longest
            count -= 1
        if total > pickup[i]:
            return [-1, -1]
    return [count, total]
