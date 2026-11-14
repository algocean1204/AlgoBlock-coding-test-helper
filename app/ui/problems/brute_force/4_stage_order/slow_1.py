# 느린 까닭: 팀 순서를 모두 만든 뒤 조건과 중복을 확인한다(12팀만 되어도 4억 8천만 가지, 23팀이면 23!가지)
from itertools import permutations


def solution(genres):
    orders = set()
    for order in permutations(genres):
        ok = True
        for i in range(len(order) - 1):
            if order[i] == order[i + 1]:
                ok = False
                break
        if ok:
            orders.add(order)
    return len(orders)
