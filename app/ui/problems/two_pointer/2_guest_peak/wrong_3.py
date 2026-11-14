# 틀린 까닭: 표시만 해 두고 누적 합으로 펼치지 않은 채 가장 큰 표시를 답으로 낸다(겹친 예약이 더해지지 않는다)
def solution(days, bookings):
    diff = [0] * (days + 2)
    for first, last, guests in bookings:
        diff[first] += guests
        diff[last + 1] -= guests
    return max(diff[1:days + 1])
