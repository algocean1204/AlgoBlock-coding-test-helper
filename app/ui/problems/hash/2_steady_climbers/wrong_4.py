# 틀린 까닭: 가장 최근의 차이만 보고 판정해, 앞에서 한 번 끊긴 손님도 꾸준한 손님으로 센다
def solution(names, days, limit):
    last = {}
    visits = {}
    fine = {}  # 마지막 차이가 limit 이하인가
    for name, day in zip(names, days):
        if name not in last:
            last[name] = day
            visits[name] = 1
        elif day != last[name]:
            fine[name] = day - last[name] <= limit
            last[name] = day
            visits[name] += 1
    return sum(1 for name in visits if visits[name] >= 2 and fine[name])
