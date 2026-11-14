# 틀린 까닭: 끝까지 본 뒤 스택에 닫히지 않은 여는 괄호가 남았는지 확인하지 않는다
def solution(expr):
    partner = {')': '(', ']': '[', '}': '{'}
    stack = []
    deepest = 0
    for ch in expr:
        if ch in '([{':
            stack.append(ch)
            deepest = max(deepest, len(stack))
        elif ch in partner:
            if not stack or stack[-1] != partner[ch]:
                return -1
            stack.pop()
    return deepest
