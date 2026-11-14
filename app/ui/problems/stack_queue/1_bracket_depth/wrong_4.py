# 틀린 까닭: 여는 괄호가 아니면 모두 닫는 괄호로 보아, 알파벳을 만나도 스택에서 꺼내려 한다
def solution(expr):
    partner = {')': '(', ']': '[', '}': '{'}
    stack = []
    deepest = 0
    for ch in expr:
        if ch in '([{':
            stack.append(ch)
            deepest = max(deepest, len(stack))
        else:
            if not stack or stack[-1] != partner.get(ch):
                return -1
            stack.pop()
    if stack:
        return -1
    return deepest
