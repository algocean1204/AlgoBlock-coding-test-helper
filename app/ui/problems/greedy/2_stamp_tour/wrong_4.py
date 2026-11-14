# 틀린 까닭: 걸린 시간의 합이 time과 같으면 넘친 것으로 본다
def solution(kinds, minutes, time):
    shortest = {}
    for kind, minute in zip(kinds, minutes):
        if kind not in shortest or minute < shortest[kind]:
            shortest[kind] = minute
    used = 0
    filled = 0
    for minute in sorted(shortest.values()):
        if used + minute >= time:
            break
        used += minute
        filled += 1
    return filled
