# 틀린 까닭: 동시에 풀린 것끼리 한 단계로 묶어 단계마다 번호 순으로 정렬해 이어 붙인다(하나를 설치하는 순간 풀린 작은 번호가 같은 단계의 큰 번호보다 먼저여야 한다)
def solution(n, rules):
    after = [[] for _ in range(n + 1)]
    waiting = [0] * (n + 1)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1
    level = [package for package in range(1, n + 1) if waiting[package] == 0]
    order = []
    while level:
        level.sort()
        order += level
        next_level = []
        for package in level:
            for nxt in after[package]:
                waiting[nxt] -= 1
                if waiting[nxt] == 0:
                    next_level.append(nxt)
        level = next_level
    if len(order) < n:
        return []
    return order
