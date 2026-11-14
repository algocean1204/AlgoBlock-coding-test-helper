# 틀린 까닭: 약속한 사람이 이미 지킨 범위 안에서 떠날 때 지킨 끝을 그 사람이 떠나는 시각으로 되돌린다
def solution(helpers, close, gap):
    people = sorted(helpers)
    reach = 0
    best = 0
    called = 0
    i = 0
    while close - reach > gap:
        while i < len(people) and people[i][0] <= reach + gap:
            arrive, leave, promised = people[i]
            if promised == 1:
                reach = leave
            else:
                best = max(best, leave)
            i += 1
        if close - reach <= gap:
            break
        if best <= reach:
            return -1
        reach = best
        called += 1
    return called
