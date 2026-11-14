# 틀린 까닭: 같은 모양의 부스를 따로 세어 부스 수를 센다(칸은 모양마다 하나다)
def solution(kinds, minutes, time):
    used = 0
    count = 0
    for minute in sorted(minutes):
        if used + minute > time:
            break
        used += minute
        count += 1
    return count
