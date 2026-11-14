# 틀린 까닭: 대표가 아니라 바로 위 부모(parent[x])끼리 비교한다(같은 묶음이어도 바로 위 부모는 다를 수 있다)
def solution(cables):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for order, (x, y) in enumerate(cables, 1):
        parent.setdefault(x, x)
        parent.setdefault(y, y)
        if parent[x] == parent[y]:
            return order
        parent[find(y)] = find(x)
    return -1
