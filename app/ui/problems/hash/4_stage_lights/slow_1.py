# 느린 까닭: 버튼마다의 상태를 적어 둔 뒤 모든 토막의 앞뒤 상태를 견준다(토막 수가 n × n / 2)
def solution(presses, m):
    states = [0]
    state = 0
    for button in presses:
        if button == 0:
            state = 0
        else:
            state ^= 1 << (button - 1)
        states.append(state)
    total = 0
    for last in range(1, len(states)):
        for first in range(last):
            if states[first] == states[last]:
                total += 1
    return total
