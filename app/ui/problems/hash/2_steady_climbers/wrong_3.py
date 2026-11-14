# 틀린 까닭: 차이가 limit과 같으면 끊긴 것으로 본다
def solution(names, days, limit):
    last = {}
    visits = {}
    broken = set()
    for name, day in zip(names, days):
        if name not in last:
            last[name] = day
            visits[name] = 1
        elif day != last[name]:
            if day - last[name] >= limit:
                broken.add(name)
            last[name] = day
            visits[name] += 1
    return sum(1 for name in visits if visits[name] >= 2 and name not in broken)
