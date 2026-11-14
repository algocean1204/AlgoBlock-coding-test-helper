# 틀린 까닭: 대표를 재귀로 찾는다(줄이 5만 칸으로 길어지면 파이썬 재귀 한도 1,000에 걸려 RecursionError가 난다)
def solution(n, merges):
    parent = list(range(n + 1))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    for a, b in merges:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_a] = root_b
    return len({find(club) for club in range(1, n + 1)})
