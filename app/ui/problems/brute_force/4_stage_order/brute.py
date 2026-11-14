from itertools import permutations


def solution(genres):
    orders = set()
    for order in permutations(genres):
        if all(order[i] != order[i + 1] for i in range(len(order) - 1)):
            orders.add(order)
    return len(orders)
