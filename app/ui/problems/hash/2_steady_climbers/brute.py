def solution(names, days, limit):
    # 손님마다 온 날을 모두 모아 서로 다른 날만 남기고, 이른 날부터 늘어놓아 정의대로 확인한다
    came = {}
    for name, day in zip(names, days):
        came.setdefault(name, set()).add(day)
    steady = 0
    for name in sorted(came):
        order = sorted(came[name])
        if len(order) >= 2 and all(order[k + 1] - order[k] <= limit for k in range(len(order) - 1)):
            steady += 1
    return steady
