# 틀린 까닭: 두 이름이 모두 앞에서 나온 적이 있으면 고리라고 본다(앞에서 나왔어도 서로 다른 묶음일 수 있다)
def solution(cables):
    seen = set()
    for order, (x, y) in enumerate(cables, 1):
        if x in seen and y in seen:
            return order
        seen.add(x)
        seen.add(y)
    return -1
