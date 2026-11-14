def solution(names, days, limit):
    last = {}  # 손님 → 마지막으로 온 날
    visits = {}  # 손님 → 서로 다른 날에 온 횟수
    broken = set()  # 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
    for name, day in zip(names, days):
        if name not in last:  # 처음 온 손님
            last[name] = day
            visits[name] = 1
        elif day != last[name]:  # 같은 날 다시 들어온 것은 새 방문이 아니다
            if day - last[name] > limit:
                broken.add(name)
            last[name] = day  # 이제 이 날이 마지막으로 온 날이다
            visits[name] += 1

    steady = 0
    for name in visits:
        if visits[name] >= 2 and name not in broken:
            steady += 1
    return steady
