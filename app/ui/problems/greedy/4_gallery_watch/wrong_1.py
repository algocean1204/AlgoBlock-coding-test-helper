# 틀린 까닭: gap을 빼먹고 빈틈 없이 덮으려 한다
def solution(helpers, close, gap):
    people = sorted(helpers)
    reach = 0
    best = 0
    called = 0
    i = 0
    while reach < close:
        while i < len(people) and people[i][0] <= reach:
            arrive, leave, promised = people[i]
            if promised == 1:
                reach = max(reach, leave)
            else:
                best = max(best, leave)
            i += 1
        if reach >= close:
            break
        if best <= reach:
            return -1
        reach = best
        called += 1
    return called
