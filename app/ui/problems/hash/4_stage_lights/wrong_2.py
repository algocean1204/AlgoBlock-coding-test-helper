# 틀린 까닭: 모두 끄는 버튼을 상태에 반영하지 않고, 토막 안에서 조명마다 짝수 번 눌렸는지만 본다
def solution(presses, m):
    seen = {0: 1}
    parity = 0
    total = 0
    for button in presses:
        if button != 0:
            parity ^= 1 << (button - 1)
        total += seen.get(parity, 0)
        seen[parity] = seen.get(parity, 0) + 1
    return total
