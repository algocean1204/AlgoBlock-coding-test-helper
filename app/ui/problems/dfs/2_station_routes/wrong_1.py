# 틀린 까닭: 돌아올 때 방문 표시를 지우지 않는다(한 갈래에서 지난 역을 다른 갈래에서 쓰지 못해 길을 적게 센다)
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
        return routes

    on_route[0] = True
    return count_from(0)
