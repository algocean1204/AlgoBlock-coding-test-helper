def solution(n, merges):
    linked = [[] for _ in range(n + 1)]
    for a, b in merges:
        linked[a].append(b)
        linked[b].append(a)
    seen = [False] * (n + 1)
    groups = 0
    for start in range(1, n + 1):
        if seen[start]:
            continue
        groups += 1
        seen[start] = True
        stack = [start]
        while stack:
            club = stack.pop()
            for other in linked[club]:
                if not seen[other]:
                    seen[other] = True
                    stack.append(other)
    return groups
