# 틀린 까닭: 모두 이어졌는지 확인하지 않는다(서로 오갈 수 없는 마을이 남아도 -1이 아니라 고른 길의 비용 합을 돌려준다)
def solution(n, roads):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = 0
    for a, b, cost in sorted(roads, key=lambda road: road[2]):
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            continue
        parent[root_b] = root_a
        total += cost
    return total
