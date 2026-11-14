# 틀린 까닭: 정렬하지 않고 주어진 순서대로 돌다가 시간이 넘치면 멈춘다
def solution(kinds, minutes, time):
    shortest = {}
    for kind, minute in zip(kinds, minutes):
        if kind not in shortest or minute < shortest[kind]:
            shortest[kind] = minute
    used = 0
    filled = 0
    for minute in shortest.values():  # 처음 나온 모양의 차례 그대로
        if used + minute > time:
            break
        used += minute
        filled += 1
    return filled
