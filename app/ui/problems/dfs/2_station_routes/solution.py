def solution(rails):
    n = len(rails)
    on_route = [False] * n  # 지금 만들고 있는 길 위에 있는 역

    def count_from(station):
        """station까지 왔을 때, 여기서 n - 1번 역까지 이어 갈 수 있는 길의 수."""
        if station == n - 1:
            return 1  # 도착: 길 하나가 완성되고 여기서 끝난다
        routes = 0
        for nxt in range(n):
            if rails[station][nxt] == 1 and not on_route[nxt]:
                on_route[nxt] = True  # 들어갈 때 표시한다
                routes += count_from(nxt)
                on_route[nxt] = False  # 돌아올 때 지운다: 다른 갈래에서 이 역을 다시 쓸 수 있게
        return routes

    on_route[0] = True  # 출발역도 길 위에 있다
    return count_from(0)
