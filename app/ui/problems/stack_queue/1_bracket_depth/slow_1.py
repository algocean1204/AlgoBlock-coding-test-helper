# 느린 까닭: 붙어 있는 (), [], {}를 지우고 처음부터 다시 찾기를 되풀이한다(겹겹이 싸인 괄호면 길이의 제곱만큼 훑는다)
def solution(expr):
    s = ''.join(ch for ch in expr if ch in '()[]{}')
    depth = 0
    deepest = 0
    for ch in s:
        if ch in '([{':
            depth += 1
            deepest = max(deepest, depth)
        else:
            depth -= 1
    while '()' in s or '[]' in s or '{}' in s:
        s = s.replace('()', '').replace('[]', '').replace('{}', '')
    if s != '':
        return -1
    return deepest
