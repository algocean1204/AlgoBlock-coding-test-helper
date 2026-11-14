# 틀린 까닭: 첫 놀이기구에도 걸어가는 시간을 더한다
from functools import cmp_to_key


def solution(fix, line, walk):
    def compare(a, b):
        return (fix[a] + walk) * line[b] - (fix[b] + walk) * line[a]

    order = sorted(range(len(fix)), key=cmp_to_key(compare))
    now = 0
    total = 0
    for ride in order:
        now += walk + fix[ride]
        total += now * line[ride]
    return total
