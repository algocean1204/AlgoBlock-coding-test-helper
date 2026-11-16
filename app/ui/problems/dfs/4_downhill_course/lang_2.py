# 언어 함정: python.missing_key
# 재귀로 쓰면: walk(hut) = 표에서 '누적 합 - target' 찾기 → 표에 넣기 → 아래 쉼터마다 walk → 표에서 빼기.
# 쉼터가 5만 개 한 줄로 이어질 수 있어 재귀가 5만 번 깊어진다. 그래서 재귀 대신,
# '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다.
def solution(trails, energy, target):
    n = len(energy)
    neighbors = [[] for _ in range(n)]
    for a, b in trails:
        neighbors[a].append(b)  # 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
        neighbors[b].append(a)
    prefix = [0] * n  # prefix[v]: 0번부터 v번까지 길 위 energy의 합
    prefix[0] = energy[0]
    # 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
    on_path = {0: 1}
    visited = [False] * n
    visited[0] = True
    count = 0
    stack = [(0, False)]  # (쉼터, 돌아오는 길인가)
    while stack:
        hut, leaving = stack.pop()
        if leaving:
            on_path[prefix[hut]] -= 1  # 이 쉼터 아래를 다 보았다: 경로에서 뺀다
            continue
        # u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
        count += on_path.get(prefix[hut] - target, 0)
        on_path[prefix[hut]] += 1
        stack.append((hut, True))  # 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
        for nxt in neighbors[hut]:
            if not visited[nxt]:
                visited[nxt] = True
                prefix[nxt] = prefix[hut] + energy[nxt]
                stack.append((nxt, False))
    return count
