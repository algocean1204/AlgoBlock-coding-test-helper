# 틀린 까닭: 비용 순으로 정렬하지 않고 주어진 순서대로 고른다(먼저 나온 비싼 길이 뒤에 나온 싼 길 자리를 차지한다)
def solution(n, roads):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = 0
    paved = 0
    for a, b, cost in roads:
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            continue
        parent[root_b] = root_a
        total += cost
        paved += 1
    if paved < n - 1:
        return -1
    return total
