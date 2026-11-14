def solution(cables):
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # 경로 압축
            x = parent[x]
        return x

    for order, (x, y) in enumerate(cables, 1):
        root_x = find(x)
        root_y = find(y)
        if root_x == root_y:
            return order
        parent[root_y] = root_x
    return -1
