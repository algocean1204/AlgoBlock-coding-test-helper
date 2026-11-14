# 느린 까닭: 쉼터마다 0번 쪽으로 한 칸씩 올라가며 합을 다시 더한다(5만 개가 한 줄로 이어지면 약 12억 번)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    up = [-1] * n
    visited = [False] * n
    visited[0] = True
    stack = [0]
    while stack:
        hut = stack.pop()
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                up[nxt] = hut
                stack.append(nxt)
    count = 0
    for v in range(n):
        total = 0
        u = v
        while u != -1:
            total += energy[u]
            if total == target:
                count += 1
            u = up[u]
    return count
