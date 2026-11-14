# 틀린 까닭: 마을마다 그 마을에 닿는 가장 싼 길 하나씩만 골라 더한다(마을끼리 짝을 이룬 묶음들이 서로 이어지지 않을 수 있다)
def solution(n, roads):
    if n == 1:
        return 0
    cheapest = {}
    for index, (a, b, cost) in enumerate(roads):
        for town in (a, b):
            if town not in cheapest or cost < roads[cheapest[town]][2]:
                cheapest[town] = index
    if len(cheapest) < n:
        return -1
    return sum(roads[index][2] for index in set(cheapest.values()))
