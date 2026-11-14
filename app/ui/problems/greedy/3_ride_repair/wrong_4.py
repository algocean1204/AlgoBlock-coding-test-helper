# 틀린 까닭: 비교 기준을 나눗셈(시간 ÷ 손님 수)으로 계산하다가 손님이 0명인 놀이기구에서 0으로 나눈다
def solution(fix, line, walk):
    order = sorted(range(len(fix)), key=lambda ride: (fix[ride] + walk) / line[ride])
    now = 0
    total = 0
    for k, ride in enumerate(order):
        if k > 0:
            now += walk
        now += fix[ride]
        total += now * line[ride]
    return total
