# 틀린 까닭: 마지막으로 온 날이 아니라 처음 온 날과의 차이를 본다
def solution(names, days, limit):
    first = {}
    seen_days = {}
    broken = set()
    for name, day in zip(names, days):
        if name not in first:
            first[name] = day
            seen_days[name] = {day}
        elif day not in seen_days[name]:
            if day - first[name] > limit:
                broken.add(name)
            seen_days[name].add(day)
    return sum(1 for name in seen_days if len(seen_days[name]) >= 2 and name not in broken)
