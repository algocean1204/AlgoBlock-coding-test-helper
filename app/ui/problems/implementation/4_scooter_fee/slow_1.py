# 느린 까닭: 회원마다 rides 전체를 처음부터 다시 훑어 그 회원의 기록을 찾는다(회원 수 × 기록 수)
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
    members = set()
    for ride in rides:
        members.add(ride.split(" ")[0])
    answer = []
    for member in members:
        total, last_end = 0, -1
        for ride in rides:
            who, start_clock, end_clock = ride.split(" ")
            if who != member:
                continue
            start, end = minutes(start_clock), minutes(end_clock)
            total += ride_fee(start, end, per_minute)
            if last_end == -1 or start - last_end > gap:
                total += unlock
            last_end = end
        answer.append([int(member), min(total, day_max)])
    answer.sort(key=lambda pair: (-pair[1], pair[0]))
    return answer
