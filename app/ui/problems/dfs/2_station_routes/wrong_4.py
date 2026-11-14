# 틀린 까닭: 들어올 때 자기 역을 표시하고 나갈 때 지우는데, 도착역에서는 바로 돌아가느라 표시를 지우지 않는다(도착역이 계속 표시되어 그 뒤의 길을 모두 놓친다)
def solution(rails):
    n = len(rails)
    on_route = [False] * n

    def count_from(station):
        on_route[station] = True
        if station == n - 1:
            return 1
        routes = 0
        for nxt in range(n):
            if rails[station][nxt] == 1 and not on_route[nxt]:
                routes += count_from(nxt)
        on_route[station] = False
        return routes

    return count_from(0)
