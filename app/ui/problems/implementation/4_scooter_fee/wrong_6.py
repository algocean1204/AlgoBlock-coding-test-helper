# 틀린 까닭: 탄 시각이 할증 시간이면 그 기록 전체를 두 배로, 아니면 전혀 두 배로 치지 않는다(겹친 분만 두 배여야 한다)
RUSH = [(7 * 60 + 30, 9 * 60 + 30), (17 * 60, 19 * 60)]


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:])


def ride_fee(start, end, per_minute):
    for rush_start, rush_end in RUSH:
        if rush_start <= start < rush_end:
            return (end - start) * per_minute * 2
    return (end - start) * per_minute


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
