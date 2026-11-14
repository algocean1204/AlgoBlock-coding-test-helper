# 느린 까닭: 경로 압축 없이 대표를 찾는다(꽂는 순서에 따라 줄이 길어져 대표 한 번 찾는 데 10만 걸음까지 걸린다)
def solution(cables):
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            x = parent[x]
        return x

    for order, (x, y) in enumerate(cables, 1):
        root_x = find(x)
        root_y = find(y)
        if root_x == root_y:
            return order
        parent[root_x] = root_y
    return -1
