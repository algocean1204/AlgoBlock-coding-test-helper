def solution(rides, price, gap):
    # 회원마다 rides 전체를 훑어 그 회원의 기록만 차례로 보고, 기록마다 1분씩 넘기며 요금을 더한다
    # (solution.py는 할증 시간과 겹친 길이를 계산한다)
    unlock, per_minute, day_max = price
    members = []
    for ride in rides:
        member = ride.split()[0]
        if member not in members:
            members.append(member)

    rows = []
    for member in members:
        fee, previous_end = 0, None
        for ride in rides:
            who, start_clock, end_clock = ride.split()
            if who != member:
                continue
            start = int(start_clock[:2]) * 60 + int(start_clock[3:])
            end = int(end_clock[:2]) * 60 + int(end_clock[3:])
            for minute in range(start, end):
                clock = f"{minute // 60:02d}:{minute % 60:02d}"
                rush = "07:30" <= clock <= "09:29" or "17:00" <= clock <= "18:59"
                fee += per_minute * (2 if rush else 1)
            if previous_end is None or start - previous_end > gap:
                fee += unlock
            previous_end = end
        rows.append([int(member), min(fee, day_max)])

    # 요금이 많은 것부터, 같으면 번호가 작은 것부터: 남은 것 가운데 가장 앞설 것을 하나씩 뽑는다
    answer = []
    while rows:
        best = rows[0]
        for row in rows:
            if row[1] > best[1] or (row[1] == best[1] and row[0] < best[0]):
                best = row
        rows.remove(best)
        answer.append(best)
    return answer
