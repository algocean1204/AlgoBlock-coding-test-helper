# 틀린 까닭: 재귀로 내려가면서 재귀 깊이 제한을 늘리지 않는다(쉼터가 한 줄로 길게 이어지면 실행 오류가 난다)
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)
        neighbors[b].append(a)
    on_path = {0: 1}
    count = 0

    def walk(hut, above, total):
        nonlocal count
        total += energy[hut]
        count += on_path.get(total - target, 0)
        on_path[total] = on_path.get(total, 0) + 1
        for nxt in neighbors[hut]:
            if nxt != above:
                walk(nxt, hut, total)
        on_path[total] -= 1

    walk(0, -1, 0)
    return count
