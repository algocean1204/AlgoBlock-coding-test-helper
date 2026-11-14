def solution(n, merges):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
            x = parent[x]
        return x

    groups = n
    for a, b in merges:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a
            groups -= 1
    return groups
