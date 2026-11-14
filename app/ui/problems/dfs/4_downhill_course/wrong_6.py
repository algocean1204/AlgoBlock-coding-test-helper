# 틀린 까닭: 지금 쉼터의 누적 합을 표에 먼저 넣고 나서 '누적 합 - target'을 찾는다(target이 0이면 빈 코스를 하나씩 더 센다)
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
        on_path[prefix[hut]] = on_path.get(prefix[hut], 0) + 1
        count += on_path.get(prefix[hut] - target, 0)
        stack.append((hut, True))
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append((nxt, False))
    return count
