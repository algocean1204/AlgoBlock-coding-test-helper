# 틀린 까닭: 같은 두 장비를 다시 잇는 경우만 고리로 본다(다른 장비를 거쳐 이미 이어진 경우를 놓친다)
def solution(cables):
    seen = set()
    for order, (x, y) in enumerate(cables, 1):
        pair = (min(x, y), max(x, y))
        if pair in seen:
            return order
        seen.add(pair)
    return -1
