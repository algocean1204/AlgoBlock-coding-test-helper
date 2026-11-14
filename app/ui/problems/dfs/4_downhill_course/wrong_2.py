# 틀린 까닭: 표를 비워 두고 시작한다(누적 합 0을 넣어 두지 않아 0번 쉼터에서 출발하는 코스를 빠뜨린다)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    prefix = [0] * n
    prefix[0] = energy[0]
    on_path = {}
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
        stack.append((hut, True))
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append((nxt, False))
    return count
