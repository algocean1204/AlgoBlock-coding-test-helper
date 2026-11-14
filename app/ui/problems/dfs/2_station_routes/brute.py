from itertools import permutations


def solution(rails):
    # 정의 그대로: 0번과 n - 1번 사이에 지날 역을 서로 다르게 골라 차례대로 늘어놓는 모든 경우를 만들고,
    # 이웃한 두 역 사이에 선로가 모두 있는 경우를 센다(같은 역을 두 번 지나지 않는 길)
    n = len(rails)
    middle = range(1, n - 1)
    total = 0
    for k in range(n - 1):
        for picked in permutations(middle, k):
            route = [0, *picked, n - 1]
            if all(rails[a][b] == 1 for a, b in zip(route, route[1:])):
                total += 1
    return total
