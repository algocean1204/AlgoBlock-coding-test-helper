# 틀린 까닭: 할증 시간의 끝(09:30, 19:00)까지 할증 시간에 넣는다('09:29까지'의 1분들인데 09:30의 1분도 넣음)
RUSH = [(7 * 60 + 30, 9 * 60 + 31), (17 * 60, 19 * 60 + 1)]


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:])


def ride_fee(start, end, per_minute):
    fee = (end - start) * per_minute
    for rush_start, rush_end in RUSH:
        fee += max(0, min(end, rush_end) - max(start, rush_start)) * per_minute
    return fee


def solution(rides, price, gap):
    unlock, per_minute, day_max = price
    total, last_end = {}, {}
    for ride in rides:
        member, start_clock, end_clock = ride.split(" ")
        start, end = minutes(start_clock), minutes(end_clock)
        fee = ride_fee(start, end, per_minute)
        if member not in last_end or start - last_end[member] > gap:
            fee += unlock
        total[member] = total.get(member, 0) + fee
        last_end[member] = end
    answer = [[int(member), min(total[member], day_max)] for member in total]
    answer.sort(key=lambda pair: (-pair[1], pair[0]))
    return answer
