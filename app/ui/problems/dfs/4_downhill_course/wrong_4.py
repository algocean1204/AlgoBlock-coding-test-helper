# 틀린 까닭: 출발 쉼터를 0번으로만 본다(중간 쉼터에서 출발하는 코스를 빠뜨린다)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    prefix = [0] * n
    prefix[0] = energy[0]
    visited = [False] * n
    visited[0] = True
    count = 0
    stack = [0]
    while stack:
        hut = stack.pop()
        if prefix[hut] == target:
            count += 1
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append(nxt)
    return count
