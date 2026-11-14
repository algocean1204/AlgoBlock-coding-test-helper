# 틀린 까닭: 고치는 시간이 짧은 놀이기구부터 고친다(손님 수를 보지 않는다)
def solution(fix, line, walk):
    order = sorted(range(len(fix)), key=lambda ride: fix[ride])
    now = 0
    total = 0
    for k, ride in enumerate(order):
        if k > 0:
            now += walk
        now += fix[ride]
        total += now * line[ride]
    return total
