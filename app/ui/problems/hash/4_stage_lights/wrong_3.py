# 틀린 까닭: 모두 끄는 버튼을 누르면 표를 비우고 새로 센다(그 버튼을 사이에 둔 토막도 제자리일 수 있다)
def solution(presses, m):
    seen = {0: 1}
    state = 0
    total = 0
    for button in presses:
        if button == 0:
            state = 0
            seen = {}
        else:
            state ^= 1 << (button - 1)
        total += seen.get(state, 0)
        seen[state] = seen.get(state, 0) + 1
    return total
