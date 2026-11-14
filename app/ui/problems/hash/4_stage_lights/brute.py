def solution(presses, m):
    # 처음부터 눌러 가며 버튼마다 조명 상태(켜짐 목록)를 그대로 적어 두고, 모든 토막의 앞뒤 상태를 견준다
    lights = [False] * (m + 1)
    states = [tuple(lights)]  # states[i]: 버튼 i개를 누른 직후의 상태
    for button in presses:
        if button == 0:
            lights = [False] * (m + 1)
        else:
            lights[button] = not lights[button]
        states.append(tuple(lights))
    count = 0
    for first in range(len(presses)):
        for last in range(first, len(presses)):
            if states[first] == states[last + 1]:
                count += 1
    return count
