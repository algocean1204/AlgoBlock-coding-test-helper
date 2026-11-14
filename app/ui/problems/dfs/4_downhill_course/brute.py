def solution(trails, energy, target):
    # 정의 그대로: 0번에서 길 수로 잰 거리로 위아래를 정하고, 쉼터 v마다 0번까지 가는 길을 만든 뒤
    # 그 길 위의 쉼터 u마다 u부터 v까지의 합을 처음부터 더해 본다
    n = len(energy)
    depth = [-1] * n
    depth[0] = 0
    changed = True
    while changed:
        changed = False
        for a, b in trails:
            if depth[a] >= 0 and depth[b] < 0:
                depth[b] = depth[a] + 1
                changed = True
            elif depth[b] >= 0 and depth[a] < 0:
                depth[a] = depth[b] + 1
                changed = True
    up = [-1] * n
    for a, b in trails:
        if depth[a] < depth[b]:
            up[b] = a
        else:
            up[a] = b
    count = 0
    for v in range(n):
        path = []  # v에서 0번까지
        k = v
        while k != -1:
            path.append(k)
            k = up[k]
        for length in range(1, len(path) + 1):  # u = path[length - 1]
            if sum(energy[hut] for hut in path[:length]) == target:
                count += 1
    return count
