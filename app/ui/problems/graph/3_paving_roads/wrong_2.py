# 틀린 까닭: 같은 묶음인지는 대표로 묻지만, 합칠 때 대표가 아닌 b번 마을을 a번 아래에 바로 잇는다(b의 원래 묶음에서 b만 떨어져 나온다)
def solution(n, roads):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = 0
    paved = 0
    for a, b, cost in sorted(roads, key=lambda road: road[2]):
        if find(a) == find(b):
            continue
        parent[b] = a
        total += cost
        paved += 1
    if paved < n - 1:
        return -1
    return total
