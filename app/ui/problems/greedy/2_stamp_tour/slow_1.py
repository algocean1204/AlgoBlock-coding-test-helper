# 느린 까닭: 칸 하나를 채울 때마다 남은 것 전체에서 가장 짧은 것을 min으로 찾고 remove로 지운다(칸 수 × 모양 수)
def solution(kinds, minutes, time):
    shortest = {}
    for kind, minute in zip(kinds, minutes):
        if kind not in shortest or minute < shortest[kind]:
            shortest[kind] = minute
    rest = list(shortest.values())
    used = 0
    filled = 0
    while rest:
        minute = min(rest)
        if used + minute > time:
            break
        rest.remove(minute)
        used += minute
        filled += 1
    return filled
