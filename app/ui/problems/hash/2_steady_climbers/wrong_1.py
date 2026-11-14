# 틀린 까닭: 같은 날 여러 번 들어온 기록을 서로 다른 방문으로 센다
def solution(names, days, limit):
    last = {}
    visits = {}
    broken = set()
    for name, day in zip(names, days):
        if name not in last:
            last[name] = day
            visits[name] = 1
        else:
            if day - last[name] > limit:
                broken.add(name)
            last[name] = day
            visits[name] += 1
    return sum(1 for name in visits if visits[name] >= 2 and name not in broken)
