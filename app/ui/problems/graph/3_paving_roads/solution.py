def solution(n, roads):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # 경로 압축
            x = parent[x]
        return x

    total = 0
    paved = 0
    for a, b, cost in sorted(roads, key=lambda road: road[2]):  # 싼 길부터 본다
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:  # 이미 오갈 수 있다: 포장하면 고리가 생긴다
            continue
        parent[root_b] = root_a
        total += cost
        paved += 1

    if paved < n - 1:  # 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
        return -1
    return total
