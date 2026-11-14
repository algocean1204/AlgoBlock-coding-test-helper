# 틀린 까닭: 표를 days + 1칸으로 만들고 1일부터 써서, last가 days일 때 last + 1일 칸이 없어 오류가 난다
def solution(days, bookings):
    diff = [0] * (days + 1)
    for first, last, guests in bookings:
        diff[first] += guests
        diff[last + 1] -= guests
    best = 0
    staying = 0
    for day in range(1, days + 1):
        staying += diff[day]
        best = max(best, staying)
    return best
