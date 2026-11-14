# 틀린 까닭: 연결 요소를 셀 때처럼 한 번 표시한 역은 다시 보지 않는 스택 탐색으로 센다(역마다 한 번밖에 들르지 못해 길을 하나밖에 만들지 못한다)
def solution(rails):
    n = len(rails)
    visited = [False] * n
    visited[0] = True
    stack = [0]
    routes = 0
    while stack:
        station = stack.pop()
        if station == n - 1:
            routes += 1
            continue
        for nxt in range(n):
            if rails[station][nxt] == 1 and not visited[nxt]:
                visited[nxt] = True
                stack.append(nxt)
    return routes
