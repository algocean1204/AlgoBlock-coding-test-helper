from itertools import permutations


def solution(fix, line, walk):
    # 고치는 차례를 모두 늘어놓고, 차례마다 기다림의 합을 글자 그대로 계산한다
    best = None
    for order in permutations(range(len(fix))):
        now = 0
        total = 0
        for k, ride in enumerate(order):
            start = 0 if k == 0 else now + walk
            now = start + fix[ride]
            total += now * line[ride]
        if best is None or total < best:
            best = total
    return best
