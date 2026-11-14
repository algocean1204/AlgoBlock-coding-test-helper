# 틀린 까닭: 빼는 표시를 last + 1일이 아니라 last일에 두어 예약의 마지막 날이 빠진다
def solution(days, bookings):
    diff = [0] * (days + 2)
    for first, last, guests in bookings:
        diff[first] += guests
        diff[last] -= guests
    best = 0
    staying = 0
    for day in range(1, days + 1):
        staying += diff[day]
        best = max(best, staying)
    return best
