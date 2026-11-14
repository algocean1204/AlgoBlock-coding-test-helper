# 틀린 까닭: '돌아올 때' 표시를 자식들보다 나중에 스택에 넣는다(먼저 꺼내져 자식을 보기도 전에 표에서 빠진다)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    prefix = [0] * n
    prefix[0] = energy[0]
    on_path = {0: 1}
    visited = [False] * n
    visited[0] = True
    count = 0
    stack = [(0, False)]
    while stack:
        hut, leaving = stack.pop()
        if leaving:
            on_path[prefix[hut]] -= 1
            continue
        count += on_path.get(prefix[hut] - target, 0)
        on_path[prefix[hut]] = on_path.get(prefix[hut], 0) + 1
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append((nxt, False))
        stack.append((hut, True))
    return count
