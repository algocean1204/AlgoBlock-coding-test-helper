def solution(days, bookings):
    best = 0
    for day in range(1, days + 1):
        staying = 0
        for first, last, guests in bookings:
            if first <= day <= last:
                staying += guests
        best = max(best, staying)
    return best
