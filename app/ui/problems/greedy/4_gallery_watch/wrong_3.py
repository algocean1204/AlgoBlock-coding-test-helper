# 틀린 까닭: 약속한 사람을 불러야 오는 사람으로 본다
def solution(helpers, close, gap):
    people = sorted(helpers)
    reach = 0
    best = 0
    called = 0
    i = 0
    while close - reach > gap:
        while i < len(people) and people[i][0] <= reach + gap:
            best = max(best, people[i][1])
            i += 1
        if best <= reach:
            return -1
        reach = best
        called += 1
    return called
