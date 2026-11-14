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
    if stack:
        return -1
    return deepest
