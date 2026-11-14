# 틀린 까닭: 아무것도 누르지 않은 처음 상태(모두 꺼짐)를 표에 넣어 두지 않는다
def solution(presses, m):
    seen = {}
    state = 0
    total = 0
    for button in presses:
        if button == 0:
            state = 0
        else:
            state ^= 1 << (button - 1)
        total += seen.get(state, 0)
        seen[state] = seen.get(state, 0) + 1
    return total
