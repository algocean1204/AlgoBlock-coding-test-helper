# 틀린 까닭: 마지막 사람이 떠난 뒤 close까지 비는 시간도 gap까지 허락되는 것을 놓치고 close까지 꼭 덮으려 한다
def solution(helpers, close, gap):
    people = sorted(helpers)
    reach = 0
    best = 0
    called = 0
    i = 0
    while reach < close:
        while i < len(people) and people[i][0] <= reach + gap:
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
