# 틀린 까닭: 간격이 꼭 gap분일 때도 잠금 해제 요금을 받는다('이하'인데 '미만'으로 옮김)
RUSH = [(7 * 60 + 30, 9 * 60 + 30), (17 * 60, 19 * 60)]


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
        if member not in last_end or start - last_end[member] >= gap:
            fee += unlock
        total[member] = total.get(member, 0) + fee
        last_end[member] = end
    answer = [[int(member), min(total[member], day_max)] for member in total]
    answer.sort(key=lambda pair: (-pair[1], pair[0]))
    return answer
