# 틀린 까닭: trails의 [a, b]에서 a를 늘 위쪽 쉼터로 본다(길에는 방향이 없어 [아래, 위]로 적힌 길을 놓친다)
def solution(trails, energy, target):
    n = len(energy)
    children = [[] for _ in range(n)]
    for a, b in trails:
        children[a].append(b)
    prefix = [0] * n
    prefix[0] = energy[0]
    on_path = {0: 1}
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
        for nxt in children[hut]:
            prefix[nxt] = prefix[hut] + energy[nxt]
            stack.append((nxt, False))
    return count
