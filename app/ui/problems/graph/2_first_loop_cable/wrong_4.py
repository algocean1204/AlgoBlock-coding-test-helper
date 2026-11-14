# 틀린 까닭: 이름에 0부터 번호를 붙이면서 parent를 '케이블 수 + 1' 크기로 잡는다(서로 떨어진 케이블만 있으면 이름이 케이블 수의 두 배까지 나와 자리가 모자란다)
def solution(cables):
    number = {}
    parent = list(range(len(cables) + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for order, (x, y) in enumerate(cables, 1):
        for name in (x, y):
            if name not in number:
                number[name] = len(number)
        root_x = find(number[x])
        root_y = find(number[y])
        if root_x == root_y:
            return order
        parent[root_y] = root_x
    return -1
