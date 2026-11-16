# 언어 함정: python.shared_rows
from collections import deque


def solution(n, cables, start, offline):
    neighbors = [[]] * (n + 1)
    for a, b in cables:
        neighbors[a].append(b)  # 케이블은 양쪽 방향이다
        neighbors[b].append(a)
    off = [False] * (n + 1)  # off[v]: v번 서버가 꺼져 있는가
    for server in offline:
        off[server] = True

    # minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
    minute = [-1] * (n + 1)
    minute[start] = 0
    queue = deque([start])
    while queue:
        server = queue.popleft()
        for nxt in neighbors[server]:
            if minute[nxt] == -1 and not off[nxt]:  # 꺼진 서버는 받지도 보내지도 않는다
                minute[nxt] = minute[server] + 1
                queue.append(nxt)

    latest = max(minute)  # start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
    return [latest, minute.count(latest)]
