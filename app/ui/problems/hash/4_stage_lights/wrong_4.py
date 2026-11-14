# 틀린 까닭: 같은 상태가 다시 나오면 1만 더한다(앞서 그 상태였던 때마다 토막이 하나씩 생긴다)
def solution(presses, m):
    seen = {0}
    state = 0
    total = 0
    for button in presses:
        if button == 0:
            state = 0
        else:
            state ^= 1 << (button - 1)
        if state in seen:
            total += 1
        seen.add(state)
    return total
