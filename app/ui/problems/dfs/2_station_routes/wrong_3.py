# 틀린 까닭: 출발역 0을 방문 표시하지 않는다(0번 역으로 되돌아왔다가 다시 나가는 길까지 센다)
def solution(rails):
    n = len(rails)
    on_route = [False] * n

    def count_from(station):
        if station == n - 1:
            return 1
        routes = 0
        for nxt in range(n):
            if rails[station][nxt] == 1 and not on_route[nxt]:
                on_route[nxt] = True
                routes += count_from(nxt)
                on_route[nxt] = False
        return routes

    return count_from(0)
