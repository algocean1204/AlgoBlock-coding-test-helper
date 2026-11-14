# 느린 까닭: 가지치기는 하지만 팀을 하나하나 따로 놓아 보고 마지막에 집합으로 중복을 없앤다(같은 순서표를 수천 번씩 다시 만든다)
def solution(genres):
    used = [False] * len(genres)
    order = []
    orders = set()

    def place():
        if len(order) == len(genres):
            orders.add(tuple(order))
            return
        for i in range(len(genres)):
            if used[i] or (order and order[-1] == genres[i]):
                continue
            used[i] = True
            order.append(genres[i])
            place()
            order.pop()
            used[i] = False

    place()
    return len(orders)
