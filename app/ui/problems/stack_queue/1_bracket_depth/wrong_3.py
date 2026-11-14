# 틀린 까닭: 닫는 괄호가 오면 맨 위를 꺼내기만 하고 같은 종류인지 확인하지 않는다
def solution(expr):
    stack = []
    deepest = 0
    for ch in expr:
        if ch in '([{':
            stack.append(ch)
            deepest = max(deepest, len(stack))
        elif ch in ')]}':
            if not stack:
                return -1
            stack.pop()
    if stack:
        return -1
    return deepest
