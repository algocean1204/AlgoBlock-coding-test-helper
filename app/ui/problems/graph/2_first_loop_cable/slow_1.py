# 느린 까닭: 케이블마다 지금까지 꽂은 케이블을 따라 x에서 갈 수 있는 장비를 처음부터 다시 찾는다(10만 개면 10만 × 10만 번)
def solution(cables):
    linked = {}
    for order, (x, y) in enumerate(cables, 1):
        seen = {x}
        stack = [x]
        while stack:
            device = stack.pop()
            for other in linked.get(device, []):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        if y in seen:
            return order
        linked.setdefault(x, []).append(y)
        linked.setdefault(y, []).append(x)
    return -1
