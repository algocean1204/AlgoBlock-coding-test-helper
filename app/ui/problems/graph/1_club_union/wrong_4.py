# 틀린 까닭: 기록에 나온 동아리만 센다(한 번도 합쳐지지 않은 동아리도 혼자서 연합 하나다)
def solution(n, merges):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in merges:
        parent.setdefault(a, a)
        parent.setdefault(b, b)
    groups = len(parent)
    for a, b in merges:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a
            groups -= 1
    return groups
