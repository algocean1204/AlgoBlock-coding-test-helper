# 틀린 까닭: 괄호 종류마다 개수만 센다(종류별로 닫는 것이 여는 것보다 많아지지만 않으면 된다고 보아 ([)]를 올바르다고 한다)
def solution(expr):
    opened = {'(': 0, '[': 0, '{': 0}
    partner = {')': '(', ']': '[', '}': '{'}
    depth = 0
    deepest = 0
    for ch in expr:
        if ch in opened:
            opened[ch] += 1
            depth += 1
            deepest = max(deepest, depth)
        elif ch in partner:
            opened[partner[ch]] -= 1
            depth -= 1
            if opened[partner[ch]] < 0:
                return -1
    if any(count != 0 for count in opened.values()):
        return -1
    return deepest
