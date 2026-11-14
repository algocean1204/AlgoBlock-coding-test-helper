# 틀린 까닭: 이어 탔는지를 같은 회원이 아니라 rides에서 바로 앞에 있는 기록(다른 회원일 수 있다)과 견주어 판단한다
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
    total, previous_end = {}, None
    for ride in rides:
        member, start_clock, end_clock = ride.split(" ")
        start, end = minutes(start_clock), minutes(end_clock)
        fee = ride_fee(start, end, per_minute)
        if previous_end is None or start - previous_end > gap:
            fee += unlock
        total[member] = total.get(member, 0) + fee
        previous_end = end
    answer = [[int(member), min(total[member], day_max)] for member in total]
    answer.sort(key=lambda pair: (-pair[1], pair[0]))
    return answer
