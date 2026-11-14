RUSH = [(7 * 60 + 30, 9 * 60 + 30), (17 * 60, 19 * 60)]  # 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)


def to_minutes(clock):
    # "HH:MM" → 자정부터 몇 분째인가
    hour, minute = clock.split(":")
    return int(hour) * 60 + int(minute)


def ride_fee(start, end, per_minute):
    # start분부터 end분 바로 전까지: 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
    fee = (end - start) * per_minute
    for rush_start, rush_end in RUSH:
        overlap = min(end, rush_end) - max(start, rush_start)
        if overlap > 0:
            fee += overlap * per_minute
    return fee


def solution(rides, price, gap):
    unlock, per_minute, day_max = price

    total = {}  # 회원 → 그날 요금 합
    last_end = {}  # 회원 → 바로 앞 기록의 끝 시각(분)
    for ride in rides:
        member, start_clock, end_clock = ride.split(" ")
        start = to_minutes(start_clock)
        end = to_minutes(end_clock)
        fee = ride_fee(start, end, per_minute)
        # 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
        if member not in last_end or start - last_end[member] > gap:
            fee += unlock
        total[member] = total.get(member, 0) + fee
        last_end[member] = end

    answer = []
    for member in total:
        answer.append([int(member), min(total[member], day_max)])  # 상한은 하루 합에 한 번
    answer.sort(key=lambda pair: (-pair[1], pair[0]))  # 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
    return answer
