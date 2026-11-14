# 틀린 까닭: 걷는 시간을 빼고 고치는 시간과 손님 수만으로 비교 기준을 세운다
from functools import cmp_to_key


def solution(fix, line, walk):
    def compare(a, b):
        return fix[a] * line[b] - fix[b] * line[a]

    order = sorted(range(len(fix)), key=cmp_to_key(compare))
    now = 0
    total = 0
    for k, ride in enumerate(order):
        if k > 0:
            now += walk
        now += fix[ride]
        total += now * line[ride]
    return total
