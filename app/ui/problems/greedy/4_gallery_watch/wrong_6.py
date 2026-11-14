# 틀린 까닭: 이어 받을 수 있는 사람 가운데 가장 오래 머무는 사람을 부른다(가장 늦게 떠나는 사람이어야 한다)
def solution(helpers, close, gap):
    people = sorted(helpers)
    reach = 0
    called = 0
    pool = []  # 이어 받을 수 있는, 불러야 오는 사람
    i = 0
    while close - reach > gap:
        while i < len(people) and people[i][0] <= reach + gap:
            arrive, leave, promised = people[i]
            if promised == 1:
                reach = max(reach, leave)
            else:
                pool.append((leave - arrive, leave))
            i += 1
        if close - reach <= gap:
            break
        useful = [item for item in pool if item[1] > reach]
        if not useful:
            return -1
        stay, leave = max(useful)
        pool.remove((stay, leave))
        reach = leave
        called += 1
    return called
