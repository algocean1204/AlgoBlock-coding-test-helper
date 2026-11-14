# 틀린 까닭: 깊이를 연달아 연 괄호의 수로 잰다(닫는 괄호가 나오면 0으로 되돌려, 아직 열려 있는 바깥 괄호를 잊는다)
def solution(expr):
    partner = {')': '(', ']': '[', '}': '{'}
    stack = []
    run = 0
    deepest = 0
    for ch in expr:
        if ch in '([{':
            stack.append(ch)
            run += 1
            deepest = max(deepest, run)
        elif ch in partner:
            run = 0
            if not stack or stack[-1] != partner[ch]:
                return -1
            stack.pop()
    if stack:
        return -1
    return deepest
