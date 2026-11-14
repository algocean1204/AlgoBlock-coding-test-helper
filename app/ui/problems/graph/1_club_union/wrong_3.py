# 틀린 까닭: 마지막에 대표를 다시 찾지 않고 parent에 남은 서로 다른 값을 센다(parent에는 대표가 아닌 중간 동아리가 남아 있을 수 있다)
def solution(n, merges):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in merges:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a
    return len(set(parent[1:]))
