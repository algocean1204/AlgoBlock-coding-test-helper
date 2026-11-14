def solution(expr):
    # 괄호만 (글자, 원래 위치)로 남긴다
    items = [(ch, i) for i, ch in enumerate(expr) if ch in '()[]{}']
    pairs = []
    # 규칙을 거꾸로: 붙어 있는 (), [], {} 한 쌍을 찾아 지우기를 더 지울 것이 없을 때까지 되풀이한다
    found = True
    while found:
        found = False
        for k in range(len(items) - 1):
            if items[k][0] + items[k + 1][0] in ('()', '[]', '{}'):
                pairs.append((items[k][1], items[k + 1][1]))
                del items[k:k + 2]
                found = True
                break
    if items:
        return -1
    # 깊이의 정의 그대로: 쌍마다 바깥에서 감싸는 쌍의 수 + 1
    deepest = 0
    for left, right in pairs:
        outside = 0
        for a, b in pairs:
            if a < left and right < b:
                outside += 1
        deepest = max(deepest, outside + 1)
    return deepest
