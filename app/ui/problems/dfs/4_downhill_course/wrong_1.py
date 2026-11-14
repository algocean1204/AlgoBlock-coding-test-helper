# 틀린 까닭: 아래를 다 보고 돌아올 때 누적 합을 표에서 빼지 않는다(먼저 둘러본 다른 갈래의 쉼터에서 출발하는 코스까지 센다)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    prefix = [0] * n
    prefix[0] = energy[0]
    seen = {0: 1}
    visited = [False] * n
    visited[0] = True
    count = 0
    stack = [0]
    while stack:
        hut = stack.pop()
        count += seen.get(prefix[hut] - target, 0)
        seen[prefix[hut]] = seen.get(prefix[hut], 0) + 1
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append(nxt)
    return count
