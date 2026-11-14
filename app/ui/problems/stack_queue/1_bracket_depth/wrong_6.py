# 틀린 까닭: 닫는 괄호가 오면 스택이 비었는지 먼저 보지 않고 맨 위를 본다(())처럼 닫는 괄호가 먼저 많아지면 빈 스택에서 IndexError가 난다)
def solution(expr):
    partner = {')': '(', ']': '[', '}': '{'}
    stack = []
    deepest = 0
    for ch in expr:
        if ch in '([{':
            stack.append(ch)
            deepest = max(deepest, len(stack))
        elif ch in partner:
            if stack[-1] != partner[ch]:
                return -1
            stack.pop()
    if stack:
        return -1
    return deepest
