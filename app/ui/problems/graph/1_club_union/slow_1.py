# 느린 까닭: 경로 압축 없이 대표를 찾는다(합치는 순서에 따라 줄이 길어져 대표 한 번 찾는 데 10만 걸음까지 걸린다)
def solution(n, merges):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    groups = n
    for a, b in merges:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            groups -= 1
    return groups
