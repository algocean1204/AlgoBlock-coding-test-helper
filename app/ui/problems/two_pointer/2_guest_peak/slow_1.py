# 느린 까닭: 예약마다 first일부터 last일까지 날을 하나씩 더한다(예약 5만 개 × 날 10만 개)
def solution(days, bookings):
    staying = [0] * (days + 1)
    for first, last, guests in bookings:
        for day in range(first, last + 1):
            staying[day] += guests
    return max(staying)
