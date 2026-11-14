# 느린 까닭: 한 명을 부를 때마다 모든 자원봉사자를 처음부터 다시 훑는다(부른 수 × 사람 수)
def solution(helpers, close, gap):
    reach = 0
    called = 0
    while close - reach > gap:
        grew = True
        while grew:  # 약속한 사람으로 늘릴 수 있는 데까지 늘린다
            grew = False
            for arrive, leave, promised in helpers:
                if promised == 1 and arrive <= reach + gap and leave > reach:
                    reach = leave
                    grew = True
        if close - reach <= gap:
            break
        best = reach
        for arrive, leave, promised in helpers:
            if promised == 0 and arrive <= reach + gap and leave > best:
                best = leave
        if best == reach:
            return -1
        reach = best
        called += 1
    return called
