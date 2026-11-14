# 틀린 까닭: 같은 연합인지는 대표로 묻지만, 합칠 때 대표가 아닌 b번 동아리를 a번 아래에 바로 잇는다(b의 원래 연합에서 b만 떨어져 나온다)
def solution(n, merges):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    groups = n
    for a, b in merges:
        if find(a) != find(b):
            parent[b] = a
            groups -= 1
    return groups
