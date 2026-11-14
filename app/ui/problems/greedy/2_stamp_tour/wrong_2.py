# 틀린 까닭: 모양마다 처음 나온 부스를 남긴다(가장 짧은 부스를 남겨야 한다)
def solution(kinds, minutes, time):
    first = {}
    for kind, minute in zip(kinds, minutes):
        if kind not in first:
            first[kind] = minute
    used = 0
    filled = 0
    for minute in sorted(first.values()):
        if used + minute > time:
            break
        used += minute
        filled += 1
    return filled
