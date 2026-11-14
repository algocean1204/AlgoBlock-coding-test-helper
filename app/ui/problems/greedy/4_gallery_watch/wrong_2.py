# 틀린 까닭: 약속한 사람도 부른 사람으로 센다
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
                reach = max(reach, leave)
                called += 1
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
