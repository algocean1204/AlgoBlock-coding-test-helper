def solution(n, cables, start, offline):
    # 큐를 쓰지 않는다: 케이블마다 '한쪽 시각 + 1'로 다른 쪽 시각을 줄이는 일을 더 바뀌지 않을 때까지 되풀이한다
    big = n + 1
    off = set(offline)
    minute = [big] * (n + 1)
    minute[start] = 0
    changed = True
    while changed:
        changed = False
        for a, b in cables:
            if a in off or b in off:
                continue
            if minute[a] + 1 < minute[b]:
                minute[b] = minute[a] + 1
                changed = True
            if minute[b] + 1 < minute[a]:
                minute[a] = minute[b] + 1
                changed = True
    got = [minute[v] for v in range(1, n + 1) if minute[v] < big]
    return [max(got), got.count(max(got))]
