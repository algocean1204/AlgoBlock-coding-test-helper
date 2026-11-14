def solution(days, bookings):
    # diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
    diff = [0] * (days + 2)
    for first, last, guests in bookings:
        diff[first] += guests
        diff[last + 1] -= guests
    # 1일부터 누적하면 그날 묵는 사람 수가 된다
    best = 0
    staying = 0
    for day in range(1, days + 1):
        staying += diff[day]
        best = max(best, staying)
    return best
