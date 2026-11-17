# 언어 함정: python.shared_rows
import heapq


def solution(n, rules):
    after = [[]] * (n + 1)  # after[a]: a를 설치해야 설치할 수 있는 패키지들
    waiting = [0] * (n + 1)  # waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
    for a, b in rules:
        after[a].append(b)
        waiting[b] += 1

    ready = [package for package in range(1, n + 1) if waiting[package] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        package = heapq.heappop(ready)
        order.append(package)
        for nxt in after[package]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                heapq.heappush(ready, nxt)

    if len(order) < n:  # 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
        return []
    return order
