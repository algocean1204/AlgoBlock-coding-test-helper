def solution(kinds, minutes, time):
    # 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
    shortest = {}
    for kind, minute in zip(kinds, minutes):
        if kind not in shortest or minute < shortest[kind]:
            shortest[kind] = minute

    used = 0  # 지금까지 쓴 시간
    filled = 0  # 채운 칸 수
    for minute in sorted(shortest.values()):  # 짧은 것부터
        if used + minute > time:
            break  # 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
        used += minute
        filled += 1
    return filled
